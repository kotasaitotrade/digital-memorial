"""
日本の民法に基づく相続計算ロジック
- 法定相続人の判定
- 法定相続分の計算（分数・パーセント）
- 遺留分の計算
"""
from fractions import Fraction
from typing import List, Dict, Any


def calculate_inheritance(family_members: List[Any], estate_value: int = 0) -> Dict:
    """
    family_members: FamilyMemberモデルのリスト
    estate_value: 正味遺産額（円）
    """
    # 続柄ごとに分類
    spouse = None
    children = []          # 放棄していない子（生存・欠格・廃除含む）
    grandchildren = []     # 代襲相続する孫（親が死亡or欠格or廃除かつ放棄していない）
    parents = []           # 直系尊属
    grandparents = []
    siblings = []          # 兄弟姉妹
    nephews_nieces = []    # 代襲甥姪

    for m in family_members:
        rel = m.relationship
        if rel == "spouse":
            if m.is_alive and not m.has_renounced:
                spouse = m
        elif rel == "child":
            if not m.has_renounced:
                children.append(m)
        elif rel == "grandchild":
            if not m.has_renounced:
                grandchildren.append(m)
        elif rel == "parent":
            if m.is_alive and not m.has_renounced:
                parents.append(m)
        elif rel == "grandparent":
            if m.is_alive and not m.has_renounced:
                grandparents.append(m)
        elif rel == "sibling":
            if not m.has_renounced:
                siblings.append(m)
        elif rel == "nephew_niece":
            if not m.has_renounced:
                nephews_nieces.append(m)

    # ─── 第1順位：子（生存）+ 代襲孫 ───────────────────────
    # 有効な子：生存 かつ 欠格でない かつ 廃除でない
    active_children = [c for c in children if c.is_alive and not c.is_disqualified]

    # 代襲対象の子（死亡 or 欠格 or 廃除 → 孫が代襲）
    proxy_child_ids = {c.id for c in children if (not c.is_alive or c.is_disqualified)}

    # 代襲孫：parent_member_id が proxy_child_ids に含まれ、欠格でない
    # グループ化（子1人→孫N人のグループ）
    grandchild_groups: dict = {}  # child_id -> [grandchildren]
    for g in grandchildren:
        if g.parent_member_id in proxy_child_ids and not g.is_disqualified:
            grandchild_groups.setdefault(g.parent_member_id, []).append(g)

    active_grandchildren = [g for gc_list in grandchild_groups.values() for g in gc_list]
    first_order = active_children + active_grandchildren

    # ─── 第2順位：直系尊属（親が優先、親が全員死亡なら祖父母）──
    if parents:
        second_order = parents
    else:
        second_order = grandparents

    # ─── 第3順位：兄弟姉妹 + 代襲甥姪 ──────────────────────
    active_siblings = [s for s in siblings if s.is_alive and not s.is_disqualified]
    proxy_sibling_ids = {s.id for s in siblings if (not s.is_alive or s.is_disqualified)}
    nephew_groups: dict = {}  # sibling_id -> [nephews/nieces]
    for n in nephews_nieces:
        if n.parent_member_id in proxy_sibling_ids and not n.is_disqualified:
            nephew_groups.setdefault(n.parent_member_id, []).append(n)
    active_nephews = [n for n_list in nephew_groups.values() for n in n_list]
    third_order = active_siblings + active_nephews

    # ─── 実際の相続人を決定 ─────────────────────────────────
    if first_order:
        blood_heirs = first_order
        order_label = "第1順位（子・孫）"
    elif second_order:
        blood_heirs = second_order
        order_label = "第2順位（直系尊属）"
    elif third_order:
        blood_heirs = third_order
        order_label = "第3順位（兄弟姉妹・甥姪）"
    else:
        blood_heirs = []
        order_label = "なし"

    heirs = []
    if spouse:
        heirs.append(spouse)
    heirs.extend(blood_heirs)

    if not heirs:
        return {
            "heirs": [],
            "shares": [],
            "total_reserved": 0,
            "reserved_shares": [],
            "order_label": "相続人なし",
            "estate_value": estate_value,
            "message": "法定相続人が見つかりませんでした。家族構成を確認してください。",
        }

    # ─── 法定相続分を計算 ────────────────────────────────────
    shares: Dict[int, Fraction] = {}

    if spouse and blood_heirs:
        if first_order:
            spouse_share = Fraction(1, 2)
            blood_total = Fraction(1, 2)
        elif second_order:
            spouse_share = Fraction(2, 3)
            blood_total = Fraction(1, 3)
        else:  # third_order
            spouse_share = Fraction(3, 4)
            blood_total = Fraction(1, 4)
        shares[spouse.id] = spouse_share

        # 血族相続人の間で均等割り（代襲・半血兄弟考慮）
        _divide_blood_shares(shares, blood_heirs, blood_total,
                             grandchild_groups=grandchild_groups if first_order else None,
                             nephew_groups=nephew_groups if third_order else None)

    elif spouse and not blood_heirs:
        shares[spouse.id] = Fraction(1, 1)
    else:
        # 配偶者なし → 血族で全部均等
        _divide_blood_shares(shares, blood_heirs, Fraction(1, 1),
                             grandchild_groups=grandchild_groups if first_order else None,
                             nephew_groups=nephew_groups if third_order else None)

    # ─── 遺留分を計算 ────────────────────────────────────────
    # 遺留分権利者：配偶者、子（孫）、直系尊属のみ（兄弟姉妹・甥姪は対象外）
    reserved_eligible_ids = set()
    if spouse:
        reserved_eligible_ids.add(spouse.id)
    for h in blood_heirs:
        if h.relationship in ("child", "grandchild", "parent", "grandparent"):
            reserved_eligible_ids.add(h.id)

    # 遺留分の総額割合
    if not spouse and all(h.relationship in ("parent", "grandparent") for h in blood_heirs):
        total_reserved_ratio = Fraction(1, 3)
    else:
        total_reserved_ratio = Fraction(1, 2)

    reserved_shares: Dict[int, Fraction] = {}
    for heir_id, share in shares.items():
        if heir_id in reserved_eligible_ids:
            reserved_shares[heir_id] = total_reserved_ratio * share

    # ─── レスポンスを組み立て ────────────────────────────────
    heir_map = {h.id: h for h in heirs}
    result_heirs = []
    for h in heirs:
        share = shares.get(h.id, Fraction(0))
        reserved = reserved_shares.get(h.id)
        result_heirs.append({
            "id": h.id,
            "name": h.name,
            "relationship": h.relationship,
            "share_fraction": f"{share.numerator}/{share.denominator}",
            "share_percent": float(share * 100),
            "share_amount": int(estate_value * float(share)) if estate_value else 0,
            "reserved_fraction": f"{reserved.numerator}/{reserved.denominator}" if reserved else None,
            "reserved_percent": float(reserved * 100) if reserved else None,
            "reserved_amount": int(estate_value * float(reserved)) if (estate_value and reserved) else 0,
            "has_reserved_right": h.id in reserved_eligible_ids,
        })

    return {
        "heirs": result_heirs,
        "order_label": order_label,
        "estate_value": estate_value,
        "total_reserved_ratio": str(total_reserved_ratio) if reserved_eligible_ids else None,
        "basic_deduction": 30_000_000 + 6_000_000 * len(result_heirs),  # 相続税基礎控除
        "message": None,
    }


def _divide_blood_shares(
    shares: Dict[int, Fraction],
    blood_heirs: List[Any],
    total: Fraction,
    grandchild_groups: dict | None = None,
    nephew_groups: dict | None = None,
) -> None:
    """
    血族相続人の間で total を均等割り
    - 代襲相続：死亡した子（兄弟）の「単位分」を孫（甥姪）が等分する
    - 半血兄弟：全血の1/2の重み
    grandchild_groups: {死亡した子のid -> [代襲孫リスト]}
    nephew_groups:     {死亡した兄弟のid -> [代襲甥姪リスト]}
    """
    if not blood_heirs:
        return

    proxy_groups = grandchild_groups or nephew_groups or {}

    # ── 代表単位（proxy グループを含む）を構築 ──────────────
    # 各単位は (weight, [heir_id, ...]) のタプル
    # 生存している子は1単位、死亡した子はそのグループが1単位
    #   ただし孫が存在する死亡子のみ単位としてカウント済み（事前にフィルタ済み）
    # 代表 id セット（孫/甥姪は proxy_groups 経由）
    proxy_ids = {hid for hid, gc_list in proxy_groups.items()}  # 死亡した子/兄弟のid
    proxied_heir_ids = {g.id for gc_list in proxy_groups.values() for g in gc_list}

    # 代表単位リスト
    units: List[tuple] = []  # (weight: Fraction, heir_ids: list[int])
    for h in blood_heirs:
        if h.id in proxied_heir_ids:
            # 孫/甥姪：後でグループとして追加するのでスキップ
            continue
        if h.id not in proxy_ids:
            # 通常の生存相続人
            w = Fraction(1, 2) if getattr(h, "is_half_blood", False) else Fraction(1, 1)
            units.append((w, [h.id]))

    # 代襲グループを単位として追加（グループ全体で1単位）
    for parent_id, gc_list in proxy_groups.items():
        if not gc_list:
            continue
        # 親の半血フラグを確認（グループの重みは元の親の重みに従う）
        parent_obj = next((h for h in blood_heirs if h.id == parent_id), None)
        w = Fraction(1, 2) if (parent_obj and getattr(parent_obj, "is_half_blood", False)) else Fraction(1, 1)
        units.append((w, [g.id for g in gc_list]))

    if not units:
        return

    total_weight = sum(w for w, _ in units)
    for weight, heir_ids in units:
        per_unit = total * weight / total_weight
        per_person = per_unit / len(heir_ids)
        for hid in heir_ids:
            shares[hid] = per_person
