"""
相続計算ロジックの単体テスト
民法に基づくすべてのケースを網羅
"""
import pytest
from fractions import Fraction
from types import SimpleNamespace
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.inheritance import calculate_inheritance


# ─── テスト用ヘルパー ─────────────────────────────────────────────

_id_counter = 0

def member(
    relationship: str,
    is_alive: bool = True,
    has_renounced: bool = False,
    is_disqualified: bool = False,
    is_adopted: bool = False,
    is_half_blood: bool = False,
    parent_member_id: int | None = None,
    name: str = "",
):
    global _id_counter
    _id_counter += 1
    return SimpleNamespace(
        id=_id_counter,
        name=name or f"{relationship}_{_id_counter}",
        relationship=relationship,
        is_alive=is_alive,
        has_renounced=has_renounced,
        is_disqualified=is_disqualified,
        is_adopted=is_adopted,
        is_half_blood=is_half_blood,
        parent_member_id=parent_member_id,
    )


def shares_of(result) -> dict:
    """heir id -> share fraction の辞書を返す"""
    return {h["id"]: Fraction(h["share_fraction"]) for h in result["heirs"]}


def reserved_of(result) -> dict:
    """heir id -> reserved fraction の辞書（権利なしはNone）"""
    return {h["id"]: (Fraction(h["reserved_fraction"]) if h["reserved_fraction"] else None)
            for h in result["heirs"]}


@pytest.fixture(autouse=True)
def reset_id():
    global _id_counter
    _id_counter = 0
    yield


# ─── 1. 相続人なし ───────────────────────────────────────────────

class TestNoHeirs:
    def test_empty_family(self):
        result = calculate_inheritance([], estate_value=10_000_000)
        assert result["heirs"] == []
        assert result.get("order_label") in ("相続人なし", None, "")
        assert result.get("message") is not None

    def test_all_renounced(self):
        members = [
            member("spouse", has_renounced=True),
            member("child", has_renounced=True),
            member("child", has_renounced=True),
        ]
        result = calculate_inheritance(members)
        assert result["heirs"] == []

    def test_all_dead_and_no_proxy(self):
        # 子が全員死亡かつ孫がいない → 第2順位へ（が親もいない）
        members = [
            member("child", is_alive=False),
        ]
        result = calculate_inheritance(members)
        assert result["heirs"] == []

    def test_spouse_dead_no_blood(self):
        members = [member("spouse", is_alive=False)]
        result = calculate_inheritance(members)
        assert result["heirs"] == []


# ─── 2. 配偶者のみ ───────────────────────────────────────────────

class TestSpouseOnly:
    def test_spouse_gets_all(self):
        sp = member("spouse")
        result = calculate_inheritance([sp], estate_value=10_000_000)
        s = shares_of(result)
        assert s[sp.id] == Fraction(1, 1)
        assert result["heirs"][0]["share_amount"] == 10_000_000

    def test_spouse_reserved_is_half(self):
        sp = member("spouse")
        result = calculate_inheritance([sp])
        r = reserved_of(result)
        assert r[sp.id] == Fraction(1, 2)


# ─── 3. 子のみ ───────────────────────────────────────────────────

class TestChildrenOnly:
    def test_single_child(self):
        c = member("child")
        result = calculate_inheritance([c])
        assert shares_of(result)[c.id] == Fraction(1, 1)

    def test_two_children_equal_split(self):
        c1 = member("child")
        c2 = member("child")
        result = calculate_inheritance([c1, c2])
        s = shares_of(result)
        assert s[c1.id] == Fraction(1, 2)
        assert s[c2.id] == Fraction(1, 2)

    def test_three_children_equal_split(self):
        children = [member("child") for _ in range(3)]
        result = calculate_inheritance(children)
        s = shares_of(result)
        for c in children:
            assert s[c.id] == Fraction(1, 3)

    def test_children_reserved_is_quarter_each(self):
        c1 = member("child")
        c2 = member("child")
        result = calculate_inheritance([c1, c2])
        r = reserved_of(result)
        # 遺留分総額 1/2、子2人で均等 → 各 1/4
        assert r[c1.id] == Fraction(1, 4)
        assert r[c2.id] == Fraction(1, 4)


# ─── 4. 配偶者 + 子 ──────────────────────────────────────────────

class TestSpouseWithChildren:
    def test_one_child(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c])
        s = shares_of(result)
        assert s[sp.id] == Fraction(1, 2)
        assert s[c.id] == Fraction(1, 2)

    def test_two_children(self):
        sp = member("spouse")
        c1 = member("child")
        c2 = member("child")
        result = calculate_inheritance([sp, c1, c2])
        s = shares_of(result)
        assert s[sp.id] == Fraction(1, 2)
        assert s[c1.id] == Fraction(1, 4)
        assert s[c2.id] == Fraction(1, 4)

    def test_three_children(self):
        sp = member("spouse")
        cs = [member("child") for _ in range(3)]
        result = calculate_inheritance([sp] + cs)
        s = shares_of(result)
        assert s[sp.id] == Fraction(1, 2)
        for c in cs:
            assert s[c.id] == Fraction(1, 6)

    def test_amount_calculation(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c], estate_value=60_000_000)
        h_map = {h["id"]: h for h in result["heirs"]}
        assert h_map[sp.id]["share_amount"] == 30_000_000
        assert h_map[c.id]["share_amount"] == 30_000_000

    def test_order_label_first(self):
        result = calculate_inheritance([member("spouse"), member("child")])
        assert "第1" in result["order_label"]

    def test_reserved_spouse_plus_child(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c])
        r = reserved_of(result)
        # 遺留分総額1/2 → 配偶者1/2*1/2=1/4、子1/2*1/2=1/4
        assert r[sp.id] == Fraction(1, 4)
        assert r[c.id] == Fraction(1, 4)


# ─── 5. 配偶者 + 直系尊属 ────────────────────────────────────────

class TestSpouseWithParents:
    def test_spouse_gets_two_thirds(self):
        sp = member("spouse")
        p = member("parent")
        result = calculate_inheritance([sp, p])
        s = shares_of(result)
        assert s[sp.id] == Fraction(2, 3)
        assert s[p.id] == Fraction(1, 3)

    def test_two_parents_split_one_third(self):
        sp = member("spouse")
        p1 = member("parent")
        p2 = member("parent")
        result = calculate_inheritance([sp, p1, p2])
        s = shares_of(result)
        assert s[sp.id] == Fraction(2, 3)
        assert s[p1.id] == Fraction(1, 6)
        assert s[p2.id] == Fraction(1, 6)

    def test_order_label_second(self):
        result = calculate_inheritance([member("spouse"), member("parent")])
        assert "第2" in result["order_label"]

    def test_reserved_parents_total_one_third(self):
        # 配偶者+直系尊属のみの場合、遺留分総額は1/2
        sp = member("spouse")
        p = member("parent")
        result = calculate_inheritance([sp, p])
        r = reserved_of(result)
        # 遺留分1/2 × 配偶者2/3 = 1/3、直系尊属1/2 × 1/3 = 1/6
        assert r[sp.id] == Fraction(1, 3)
        assert r[p.id] == Fraction(1, 6)


# ─── 6. 直系尊属のみ（親のみ） ───────────────────────────────────

class TestParentsOnly:
    def test_one_parent(self):
        p = member("parent")
        result = calculate_inheritance([p])
        assert shares_of(result)[p.id] == Fraction(1, 1)

    def test_two_parents_equal(self):
        p1 = member("parent")
        p2 = member("parent")
        result = calculate_inheritance([p1, p2])
        s = shares_of(result)
        assert s[p1.id] == Fraction(1, 2)
        assert s[p2.id] == Fraction(1, 2)

    def test_parent_reserved_one_third(self):
        # 直系尊属のみ → 遺留分総額1/3
        p = member("parent")
        result = calculate_inheritance([p])
        r = reserved_of(result)
        assert r[p.id] == Fraction(1, 3)

    def test_grandparents_when_no_parents(self):
        gp1 = member("grandparent")
        gp2 = member("grandparent")
        result = calculate_inheritance([gp1, gp2])
        s = shares_of(result)
        assert s[gp1.id] == Fraction(1, 2)
        assert s[gp2.id] == Fraction(1, 2)
        assert "第2" in result["order_label"]


# ─── 7. 配偶者 + 兄弟姉妹 ────────────────────────────────────────

class TestSpouseWithSiblings:
    def test_spouse_gets_three_quarters(self):
        sp = member("spouse")
        sib = member("sibling")
        result = calculate_inheritance([sp, sib])
        s = shares_of(result)
        assert s[sp.id] == Fraction(3, 4)
        assert s[sib.id] == Fraction(1, 4)

    def test_two_siblings_split_one_quarter(self):
        sp = member("spouse")
        s1 = member("sibling")
        s2 = member("sibling")
        result = calculate_inheritance([sp, s1, s2])
        s = shares_of(result)
        assert s[sp.id] == Fraction(3, 4)
        assert s[s1.id] == Fraction(1, 8)
        assert s[s2.id] == Fraction(1, 8)

    def test_siblings_have_no_reserved_right(self):
        sp = member("spouse")
        sib = member("sibling")
        result = calculate_inheritance([sp, sib])
        r = reserved_of(result)
        # 兄弟姉妹には遺留分なし
        assert r[sib.id] is None
        # 配偶者は有り
        assert r[sp.id] is not None

    def test_order_label_third(self):
        result = calculate_inheritance([member("spouse"), member("sibling")])
        assert "第3" in result["order_label"]


# ─── 8. 兄弟姉妹のみ ────────────────────────────────────────────

class TestSiblingsOnly:
    def test_single_sibling(self):
        sib = member("sibling")
        result = calculate_inheritance([sib])
        assert shares_of(result)[sib.id] == Fraction(1, 1)

    def test_two_siblings_equal(self):
        s1 = member("sibling")
        s2 = member("sibling")
        result = calculate_inheritance([s1, s2])
        s = shares_of(result)
        assert s[s1.id] == Fraction(1, 2)
        assert s[s2.id] == Fraction(1, 2)

    def test_sibling_no_reserved_right(self):
        sib = member("sibling")
        result = calculate_inheritance([sib])
        r = reserved_of(result)
        assert r[sib.id] is None

    def test_sibling_has_reserved_right_false(self):
        sib = member("sibling")
        result = calculate_inheritance([sib])
        assert result["heirs"][0]["has_reserved_right"] is False


# ─── 9. 代襲相続（子が死亡） ────────────────────────────────────

class TestProxyInheritanceChildDead:
    def test_grandchild_inherits_dead_childs_share(self):
        sp = member("spouse")
        c_alive = member("child")
        c_dead = member("child", is_alive=False)
        gc = member("grandchild", parent_member_id=c_dead.id)
        result = calculate_inheritance([sp, c_alive, c_dead, gc])
        s = shares_of(result)
        # 配偶者1/2、子1/4、孫(代襲)1/4
        assert s[sp.id] == Fraction(1, 2)
        assert s[c_alive.id] == Fraction(1, 4)
        assert s[gc.id] == Fraction(1, 4)
        assert c_dead.id not in s  # 死亡した子は相続人でない

    def test_two_grandchildren_split_dead_parents_share(self):
        c_dead = member("child", is_alive=False)
        gc1 = member("grandchild", parent_member_id=c_dead.id)
        gc2 = member("grandchild", parent_member_id=c_dead.id)
        result = calculate_inheritance([c_dead, gc1, gc2])
        s = shares_of(result)
        # 子1人分=1/1→孫2人で1/2ずつ
        assert s[gc1.id] == Fraction(1, 2)
        assert s[gc2.id] == Fraction(1, 2)

    def test_all_children_dead_grandchildren_inherit(self):
        c1 = member("child", is_alive=False)
        c2 = member("child", is_alive=False)
        gc1 = member("grandchild", parent_member_id=c1.id)
        gc2 = member("grandchild", parent_member_id=c2.id)
        result = calculate_inheritance([c1, c2, gc1, gc2])
        s = shares_of(result)
        assert s[gc1.id] == Fraction(1, 2)
        assert s[gc2.id] == Fraction(1, 2)
        assert "第1" in result["order_label"]

    def test_grandchild_with_no_link_does_not_inherit(self):
        # parent_member_id が死亡した子のIDと一致しない孫は代襲しない
        c_dead = member("child", is_alive=False)
        gc = member("grandchild", parent_member_id=9999)  # 関係のないID
        result = calculate_inheritance([c_dead, gc])
        assert result["heirs"] == []  # 代襲されないので相続人なし


# ─── 10. 代襲相続（子が欠格） ───────────────────────────────────

class TestProxyInheritanceChildDisqualified:
    def test_disqualified_child_grandchild_inherits(self):
        c_disq = member("child", is_disqualified=True)
        gc = member("grandchild", parent_member_id=c_disq.id)
        result = calculate_inheritance([c_disq, gc])
        s = shares_of(result)
        # 欠格した子は相続できないが孫が代襲
        assert c_disq.id not in s
        assert s[gc.id] == Fraction(1, 1)

    def test_disqualified_child_spouse_and_grandchild(self):
        sp = member("spouse")
        c_disq = member("child", is_disqualified=True)
        gc = member("grandchild", parent_member_id=c_disq.id)
        result = calculate_inheritance([sp, c_disq, gc])
        s = shares_of(result)
        assert s[sp.id] == Fraction(1, 2)
        assert s[gc.id] == Fraction(1, 2)


# ─── 11. 代襲相続なし（子が相続放棄） ───────────────────────────

class TestNoProxyWhenChildRenounced:
    def test_renounced_child_no_proxy(self):
        # 放棄した子の孫は代襲しない（民法887条2項）
        c_renounced = member("child", has_renounced=True)
        gc = member("grandchild", parent_member_id=c_renounced.id)
        result = calculate_inheritance([c_renounced, gc])
        # 代襲なし → 相続人なし（他に相続人がいないため）
        assert result["heirs"] == []

    def test_renounced_child_other_child_inherits(self):
        c_ok = member("child")
        c_renounced = member("child", has_renounced=True)
        gc = member("grandchild", parent_member_id=c_renounced.id)
        result = calculate_inheritance([c_ok, c_renounced, gc])
        s = shares_of(result)
        # c_ok のみが相続（c_renounced も gc も相続しない）
        assert len(result["heirs"]) == 1
        assert s[c_ok.id] == Fraction(1, 1)

    def test_renounced_spouse_excluded(self):
        sp = member("spouse", has_renounced=True)
        c = member("child")
        result = calculate_inheritance([sp, c])
        # 配偶者は相続放棄したので含まれない
        ids = {h["id"] for h in result["heirs"]}
        assert sp.id not in ids
        assert c.id in ids


# ─── 12. 半血兄弟姉妹 ───────────────────────────────────────────

class TestHalfBloodSiblings:
    def test_half_blood_gets_half_of_full(self):
        s_full = member("sibling")
        s_half = member("sibling", is_half_blood=True)
        result = calculate_inheritance([s_full, s_half])
        s = shares_of(result)
        # 全血:半血 = 2:1 → 全血2/3、半血1/3
        assert s[s_full.id] == Fraction(2, 3)
        assert s[s_half.id] == Fraction(1, 3)

    def test_two_full_one_half(self):
        sf1 = member("sibling")
        sf2 = member("sibling")
        sh = member("sibling", is_half_blood=True)
        result = calculate_inheritance([sf1, sf2, sh])
        s = shares_of(result)
        # 全血2+半血1 = 5ユニット(全血1=2ユニット×2, 半血=1ユニット)
        # sf1=2/5, sf2=2/5, sh=1/5
        assert s[sf1.id] == Fraction(2, 5)
        assert s[sf2.id] == Fraction(2, 5)
        assert s[sh.id] == Fraction(1, 5)

    def test_half_blood_with_spouse(self):
        sp = member("spouse")
        sf = member("sibling")
        sh = member("sibling", is_half_blood=True)
        result = calculate_inheritance([sp, sf, sh])
        s = shares_of(result)
        # 配偶者3/4、兄弟の合計1/4 → 全血:半血=2:1 → sf=1/6, sh=1/12
        assert s[sp.id] == Fraction(3, 4)
        assert s[sf.id] == Fraction(1, 6)
        assert s[sh.id] == Fraction(1, 12)

    def test_only_half_blood_siblings_equal_among_themselves(self):
        sh1 = member("sibling", is_half_blood=True)
        sh2 = member("sibling", is_half_blood=True)
        result = calculate_inheritance([sh1, sh2])
        s = shares_of(result)
        # 半血同士は平等
        assert s[sh1.id] == Fraction(1, 2)
        assert s[sh2.id] == Fraction(1, 2)


# ─── 13. 養子 ───────────────────────────────────────────────────

class TestAdoptedChild:
    def test_adopted_child_same_as_biological(self):
        c_bio = member("child")
        c_adopted = member("child", is_adopted=True)
        result = calculate_inheritance([c_bio, c_adopted])
        s = shares_of(result)
        # 養子も同等の相続分
        assert s[c_bio.id] == Fraction(1, 2)
        assert s[c_adopted.id] == Fraction(1, 2)

    def test_adopted_child_reserved_right(self):
        c = member("child", is_adopted=True)
        result = calculate_inheritance([c])
        r = reserved_of(result)
        assert r[c.id] == Fraction(1, 2)  # 遺留分あり


# ─── 14. 甥姪代襲（兄弟姉妹が死亡） ─────────────────────────────

class TestNephewNieceProxy:
    def test_nephew_inherits_dead_siblings_share(self):
        sib_dead = member("sibling", is_alive=False)
        nephew = member("nephew_niece", parent_member_id=sib_dead.id)
        result = calculate_inheritance([sib_dead, nephew])
        s = shares_of(result)
        assert s[nephew.id] == Fraction(1, 1)

    def test_nephew_with_living_sibling(self):
        sib_alive = member("sibling")
        sib_dead = member("sibling", is_alive=False)
        nephew = member("nephew_niece", parent_member_id=sib_dead.id)
        result = calculate_inheritance([sib_alive, sib_dead, nephew])
        s = shares_of(result)
        assert s[sib_alive.id] == Fraction(1, 2)
        assert s[nephew.id] == Fraction(1, 2)

    def test_nephews_no_reserved_right(self):
        sib_dead = member("sibling", is_alive=False)
        nephew = member("nephew_niece", parent_member_id=sib_dead.id)
        result = calculate_inheritance([sib_dead, nephew])
        r = reserved_of(result)
        assert r[nephew.id] is None


# ─── 15. 順位飛ばし（第1→第2→第3） ─────────────────────────────

class TestOrderPriority:
    def test_child_takes_priority_over_parent(self):
        c = member("child")
        p = member("parent")
        result = calculate_inheritance([c, p])
        s = shares_of(result)
        # 子がいれば親は相続しない
        assert s[c.id] == Fraction(1, 1)
        assert p.id not in s

    def test_child_takes_priority_over_sibling(self):
        c = member("child")
        sib = member("sibling")
        result = calculate_inheritance([c, sib])
        s = shares_of(result)
        assert s[c.id] == Fraction(1, 1)
        assert sib.id not in s

    def test_parent_takes_priority_over_sibling(self):
        p = member("parent")
        sib = member("sibling")
        result = calculate_inheritance([p, sib])
        s = shares_of(result)
        assert s[p.id] == Fraction(1, 1)
        assert sib.id not in s

    def test_all_orders_present_first_wins(self):
        c = member("child")
        p = member("parent")
        sib = member("sibling")
        result = calculate_inheritance([c, p, sib])
        s = shares_of(result)
        assert s[c.id] == Fraction(1, 1)
        assert p.id not in s
        assert sib.id not in s

    def test_child_dead_no_grandchild_parent_inherits(self):
        # 子が死亡かつ孫がいない → 第2順位（親）へ
        c = member("child", is_alive=False)
        p = member("parent")
        result = calculate_inheritance([c, p])
        s = shares_of(result)
        assert s[p.id] == Fraction(1, 1)
        assert "第2" in result["order_label"]

    def test_child_renounced_parent_inherits(self):
        # 子が放棄かつ孫が代襲しない → 第2順位
        c = member("child", has_renounced=True)
        p = member("parent")
        result = calculate_inheritance([c, p])
        s = shares_of(result)
        assert s[p.id] == Fraction(1, 1)


# ─── 16. 遺留分計算 ─────────────────────────────────────────────

class TestReservedPortion:
    def test_total_ratio_half_for_spouse_children(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c])
        assert result["total_reserved_ratio"] == "1/2"

    def test_total_ratio_one_third_for_ancestors_only(self):
        p = member("parent")
        result = calculate_inheritance([p])
        assert result["total_reserved_ratio"] == "1/3"

    def test_no_reserved_for_siblings_only(self):
        sib = member("sibling")
        result = calculate_inheritance([sib])
        # 兄弟だけなら reserved ratio は None（権利者なし）
        assert result["total_reserved_ratio"] is None

    def test_spouse_only_reserved_is_half(self):
        sp = member("spouse")
        result = calculate_inheritance([sp])
        r = reserved_of(result)
        assert r[sp.id] == Fraction(1, 2)

    def test_single_child_reserved_is_half(self):
        c = member("child")
        result = calculate_inheritance([c])
        r = reserved_of(result)
        assert r[c.id] == Fraction(1, 2)

    def test_reserved_amount_correct(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c], estate_value=100_000_000)
        h_map = {h["id"]: h for h in result["heirs"]}
        # 遺留分: 配偶者=1/4=25,000,000, 子=1/4=25,000,000
        assert h_map[sp.id]["reserved_amount"] == 25_000_000
        assert h_map[c.id]["reserved_amount"] == 25_000_000


# ─── 17. 基礎控除計算 ───────────────────────────────────────────

class TestBasicDeduction:
    def test_deduction_formula(self):
        # 3,000万 + 600万×相続人数
        sp = member("spouse")
        c1 = member("child")
        c2 = member("child")
        result = calculate_inheritance([sp, c1, c2])
        # 相続人3人 → 3000 + 600×3 = 4800万
        assert result["basic_deduction"] == 48_000_000

    def test_deduction_single_heir(self):
        sp = member("spouse")
        result = calculate_inheritance([sp])
        assert result["basic_deduction"] == 36_000_000  # 3000+600=3600万

    def test_deduction_four_heirs(self):
        cs = [member("child") for _ in range(4)]
        result = calculate_inheritance(cs)
        assert result["basic_deduction"] == 54_000_000  # 3000+600×4=5400万


# ─── 18. 財産額の計算 ───────────────────────────────────────────

class TestEstateValue:
    def test_zero_estate_value_fractions_still_calculated(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c], estate_value=0)
        s = shares_of(result)
        # 金額が0でも割合は正しく計算される
        assert s[sp.id] == Fraction(1, 2)
        assert s[c.id] == Fraction(1, 2)

    def test_zero_estate_amount_is_zero(self):
        sp = member("spouse")
        result = calculate_inheritance([sp], estate_value=0)
        assert result["heirs"][0]["share_amount"] == 0

    def test_large_estate(self):
        sp = member("spouse")
        c = member("child")
        result = calculate_inheritance([sp, c], estate_value=1_000_000_000)
        h_map = {h["id"]: h for h in result["heirs"]}
        assert h_map[sp.id]["share_amount"] == 500_000_000
        assert h_map[c.id]["share_amount"] == 500_000_000


# ─── 19. 複合ケース ──────────────────────────────────────────────

class TestComplexCases:
    def test_spouse_child_dead_grandchild_proxy(self):
        # 配偶者 + 長男(生存) + 次男(死亡) + 孫(次男の子)
        sp = member("spouse")
        c1 = member("child")
        c2 = member("child", is_alive=False)
        gc = member("grandchild", parent_member_id=c2.id)
        result = calculate_inheritance([sp, c1, c2, gc], estate_value=60_000_000)
        s = shares_of(result)
        h_map = {h["id"]: h for h in result["heirs"]}
        assert s[sp.id] == Fraction(1, 2)   # 3000万
        assert s[c1.id] == Fraction(1, 4)   # 1500万
        assert s[gc.id] == Fraction(1, 4)   # 1500万 (代襲)
        assert c2.id not in s
        assert h_map[sp.id]["share_amount"] == 30_000_000

    def test_all_first_order_disqualified_no_grandchildren(self):
        # 全子供が欠格かつ孫がいない → 第2順位
        c = member("child", is_disqualified=True)
        p = member("parent")
        result = calculate_inheritance([c, p])
        s = shares_of(result)
        assert p.id in s
        assert s[p.id] == Fraction(1, 1)

    def test_full_family_with_deceased_child_and_half_sibling(self):
        # 配偶者 + 子1(生存) + 子2(死亡、孫2人) → 兄弟は相続しない
        sp = member("spouse")
        c1 = member("child")
        c2 = member("child", is_alive=False)
        gc1 = member("grandchild", parent_member_id=c2.id)
        gc2 = member("grandchild", parent_member_id=c2.id)
        sib = member("sibling")  # 第1順位がいるので相続しない
        result = calculate_inheritance([sp, c1, c2, gc1, gc2, sib])
        s = shares_of(result)
        assert s[sp.id] == Fraction(1, 2)
        assert s[c1.id] == Fraction(1, 4)
        assert s[gc1.id] == Fraction(1, 8)
        assert s[gc2.id] == Fraction(1, 8)
        assert sib.id not in s

    def test_multiple_proxy_different_grandchildren_counts(self):
        # 子A死亡(孫1人) + 子B死亡(孫2人) → 孫の代襲分は各親の分を等分
        ca = member("child", is_alive=False)
        cb = member("child", is_alive=False)
        gca = member("grandchild", parent_member_id=ca.id)
        gcb1 = member("grandchild", parent_member_id=cb.id)
        gcb2 = member("grandchild", parent_member_id=cb.id)
        result = calculate_inheritance([ca, cb, gca, gcb1, gcb2])
        s = shares_of(result)
        # 子2人で均等 → ca分=1/2, cb分=1/2
        # gca=1/2, gcb1=1/4, gcb2=1/4
        assert s[gca.id] == Fraction(1, 2)
        assert s[gcb1.id] == Fraction(1, 4)
        assert s[gcb2.id] == Fraction(1, 4)
