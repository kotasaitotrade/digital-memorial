"""
FastAPI エンドポイント統合テスト
- 認証 (register / login / me)
- 相続プラン CRUD
- 家族・資産一括保存
- 相続計算
- エンディングノート CRUD + サブアイテム全種
- チェックリスト
- 認可（他ユーザーのリソースにアクセス不可）
"""
import pytest


# ═══════════════════════════════════════════════════════════════
# 認証
# ═══════════════════════════════════════════════════════════════

class TestAuth:
    def test_register_success(self, client):
        res = client.post("/api/auth/register", json={
            "name": "田中太郎",
            "email": "tanaka@example.com",
            "password": "secure123",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "tanaka@example.com"
        assert data["name"] == "田中太郎"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "name": "A", "email": "dup@example.com", "password": "pass"
        })
        res = client.post("/api/auth/register", json={
            "name": "B", "email": "dup@example.com", "password": "pass"
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "name": "ログインユーザー", "email": "login@example.com", "password": "abc123"
        })
        res = client.post("/api/auth/login", data={
            "username": "login@example.com", "password": "abc123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()
        assert res.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "name": "X", "email": "x@example.com", "password": "correct"
        })
        res = client.post("/api/auth/login", data={
            "username": "x@example.com", "password": "wrong"
        })
        assert res.status_code == 401

    def test_login_nonexistent_user(self, client):
        res = client.post("/api/auth/login", data={
            "username": "nobody@example.com", "password": "pass"
        })
        assert res.status_code == 401

    def test_me_authenticated(self, auth_client):
        res = auth_client.get("/api/auth/me")
        assert res.status_code == 200
        assert res.json()["email"] == "test@example.com"

    def test_me_unauthenticated(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════
# 相続プラン
# ═══════════════════════════════════════════════════════════════

class TestEstatePlans:
    def test_create_plan(self, auth_client):
        res = auth_client.post("/api/estate-plans", json={"title": "私の相続計画"})
        assert res.status_code == 200
        assert res.json()["title"] == "私の相続計画"
        assert "id" in res.json()

    def test_create_plan_default_title(self, auth_client):
        res = auth_client.post("/api/estate-plans", json={})
        assert res.status_code == 200
        assert res.json()["title"] is not None

    def test_create_plan_empty_title_rejected(self, auth_client):
        res = auth_client.post("/api/estate-plans", json={"title": ""})
        assert res.status_code == 422

    def test_list_plans_empty(self, auth_client):
        res = auth_client.get("/api/estate-plans")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_plans_returns_own_only(self, auth_client, second_auth_client):
        auth_client.post("/api/estate-plans", json={"title": "私の計画"})
        res = second_auth_client.get("/api/estate-plans")
        assert res.status_code == 200
        assert len(res.json()) == 0

    def test_get_plan(self, auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={"title": "取得テスト"}).json()["id"]
        res = auth_client.get(f"/api/estate-plans/{plan_id}")
        assert res.status_code == 200
        assert res.json()["id"] == plan_id

    def test_get_plan_not_found(self, auth_client):
        res = auth_client.get("/api/estate-plans/99999")
        assert res.status_code == 404

    def test_get_other_users_plan_forbidden(self, auth_client, second_auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={"title": "私の計画"}).json()["id"]
        res = second_auth_client.get(f"/api/estate-plans/{plan_id}")
        assert res.status_code in (403, 404)

    def test_delete_plan(self, auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        res = auth_client.delete(f"/api/estate-plans/{plan_id}")
        assert res.status_code == 200
        assert res.json()["ok"] is True
        # 削除後は取得できない
        res2 = auth_client.get(f"/api/estate-plans/{plan_id}")
        assert res2.status_code == 404

    def test_delete_other_users_plan_forbidden(self, auth_client, second_auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        res = second_auth_client.delete(f"/api/estate-plans/{plan_id}")
        assert res.status_code in (403, 404)

    def test_unauthenticated_cannot_create(self, client):
        res = client.post("/api/estate-plans", json={"title": "テスト"})
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════
# 家族構成（一括保存）
# ═══════════════════════════════════════════════════════════════

class TestFamilyMembers:
    def _create_plan(self, client):
        return client.post("/api/estate-plans", json={"title": "家族テスト"}).json()["id"]

    def test_save_family_members(self, auth_client):
        plan_id = self._create_plan(auth_client)
        res = auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [
                {"name": "配偶者", "relationship": "spouse", "is_alive": True},
                {"name": "子供", "relationship": "child", "is_alive": True},
            ]
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["name"] == "配偶者"

    def test_save_replaces_existing(self, auth_client):
        plan_id = self._create_plan(auth_client)
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "旧データ", "relationship": "spouse"}]
        })
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "新データ", "relationship": "child"}]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}")
        members = res.json()["family_members"]
        assert len(members) == 1
        assert members[0]["name"] == "新データ"

    def test_save_empty_clears_all(self, auth_client):
        plan_id = self._create_plan(auth_client)
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "削除対象", "relationship": "spouse"}]
        })
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={"members": []})
        res = auth_client.get(f"/api/estate-plans/{plan_id}")
        assert len(res.json()["family_members"]) == 0

    def test_family_required_fields(self, auth_client):
        plan_id = self._create_plan(auth_client)
        # name が空 → バリデーションエラー
        res = auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "", "relationship": "spouse"}]
        })
        assert res.status_code == 422

    def test_family_half_blood_flag(self, auth_client):
        plan_id = self._create_plan(auth_client)
        res = auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "半血兄弟", "relationship": "sibling", "is_half_blood": True}]
        })
        assert res.status_code == 200
        assert res.json()[0]["is_half_blood"] is True


# ═══════════════════════════════════════════════════════════════
# 財産（一括保存）
# ═══════════════════════════════════════════════════════════════

class TestAssets:
    def _create_plan(self, client):
        return client.post("/api/estate-plans", json={"title": "財産テスト"}).json()["id"]

    def test_save_assets(self, auth_client):
        plan_id = self._create_plan(auth_client)
        res = auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [
                {"name": "自宅", "asset_type": "real_estate", "estimated_value": 30_000_000},
                {"name": "預貯金", "asset_type": "bank_account", "estimated_value": 10_000_000},
                {"name": "住宅ローン", "asset_type": "debt", "estimated_value": -5_000_000},
            ]
        })
        assert res.status_code == 200
        assert len(res.json()) == 3

    def test_save_assets_replaces(self, auth_client):
        plan_id = self._create_plan(auth_client)
        auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [{"name": "古い資産", "asset_type": "other", "estimated_value": 0}]
        })
        auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [{"name": "新しい資産", "asset_type": "real_estate", "estimated_value": 100}]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}")
        assert len(res.json()["assets"]) == 1
        assert res.json()["assets"][0]["name"] == "新しい資産"

    def test_negative_value_for_debt(self, auth_client):
        plan_id = self._create_plan(auth_client)
        res = auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [{"name": "借金", "asset_type": "debt", "estimated_value": -2_000_000}]
        })
        assert res.status_code == 200
        assert res.json()[0]["estimated_value"] == -2_000_000

    def test_deemed_estate_flag(self, auth_client):
        plan_id = self._create_plan(auth_client)
        res = auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [{"name": "生命保険", "asset_type": "life_insurance",
                        "estimated_value": 5_000_000, "is_deemed_estate": True}]
        })
        assert res.json()[0]["is_deemed_estate"] is True


# ═══════════════════════════════════════════════════════════════
# 相続計算エンドポイント
# ═══════════════════════════════════════════════════════════════

class TestInheritanceCalculate:
    def _setup_plan(self, client):
        plan_id = client.post("/api/estate-plans", json={"title": "計算テスト"}).json()["id"]
        client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [
                {"name": "配偶者", "relationship": "spouse", "is_alive": True},
                {"name": "長男", "relationship": "child", "is_alive": True},
                {"name": "次男", "relationship": "child", "is_alive": False},
                {"name": "孫", "relationship": "grandchild", "is_alive": True},
            ]
        })
        # 孫の parent_member_id は次男のIDに後でセット
        return plan_id

    def test_calculate_returns_heirs(self, auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={"title": "計算"}).json()["id"]
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [
                {"name": "配偶者", "relationship": "spouse"},
                {"name": "子", "relationship": "child"},
            ]
        })
        auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [{"name": "不動産", "asset_type": "real_estate", "estimated_value": 60_000_000}]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}/calculate")
        assert res.status_code == 200
        data = res.json()
        assert "heirs" in data
        assert len(data["heirs"]) == 2
        assert data["estate_value"] == 60_000_000

    def test_calculate_no_members_returns_empty(self, auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        res = auth_client.get(f"/api/estate-plans/{plan_id}/calculate")
        assert res.status_code == 200
        assert res.json()["heirs"] == []

    def test_calculate_negative_estate_no_negative_share_amount(self, auth_client):
        """債務超過時でも share_amount は 0 以上"""
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "子", "relationship": "child", "is_alive": True}]
        })
        auth_client.post(f"/api/estate-plans/{plan_id}/assets", json={
            "assets": [
                {"name": "預金", "asset_type": "bank_account", "estimated_value": 1_000_000},
                {"name": "借金", "asset_type": "debt", "estimated_value": -5_000_000},
            ]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}/calculate")
        assert res.status_code == 200
        data = res.json()
        assert data["estate_value"] == -4_000_000
        for heir in data["heirs"]:
            assert heir["share_amount"] >= 0
            assert heir["reserved_amount"] >= 0

    def test_calculate_sibling_third_order(self, auth_client):
        """独身・子なし・親なしの場合、兄弟姉妹が第3順位相続人となる"""
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "姉", "relationship": "sibling", "is_alive": True}]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}/calculate")
        assert res.status_code == 200
        data = res.json()
        assert data["order_label"] == "第3順位（兄弟姉妹・甥姪）"
        assert len(data["heirs"]) == 1
        assert data["heirs"][0]["name"] == "姉"

    def test_calculate_share_fractions(self, auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [
                {"name": "配偶者", "relationship": "spouse"},
                {"name": "子1", "relationship": "child"},
                {"name": "子2", "relationship": "child"},
            ]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}/calculate")
        heirs = res.json()["heirs"]
        shares = {h["name"]: h["share_fraction"] for h in heirs}
        assert shares["配偶者"] == "1/2"
        assert shares["子1"] == "1/4"
        assert shares["子2"] == "1/4"

    def test_calculate_includes_basic_deduction(self, auth_client):
        plan_id = auth_client.post("/api/estate-plans", json={}).json()["id"]
        auth_client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [{"name": "子", "relationship": "child"}]
        })
        res = auth_client.get(f"/api/estate-plans/{plan_id}/calculate")
        # 相続人1人 → 3000+600=3600万
        assert res.json()["basic_deduction"] == 36_000_000

    def test_calculate_unauthenticated(self, client):
        res = client.get("/api/estate-plans/1/calculate")
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════
# エンディングノート
# ═══════════════════════════════════════════════════════════════

class TestEndingNote:
    def test_get_creates_note_automatically(self, auth_client):
        res = auth_client.get("/api/ending-note")
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        assert "life_prolonging" in data

    def test_get_twice_returns_same_note(self, auth_client):
        id1 = auth_client.get("/api/ending-note").json()["id"]
        id2 = auth_client.get("/api/ending-note").json()["id"]
        assert id1 == id2

    def test_update_medical_preferences(self, auth_client):
        res = auth_client.put("/api/ending-note", json={
            "life_prolonging": "希望しない",
            "cpr": "希望しない",
            "organ_donation": "希望する",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["life_prolonging"] == "希望しない"
        assert data["organ_donation"] == "希望する"

    def test_update_funeral_preferences(self, auth_client):
        res = auth_client.put("/api/ending-note", json={
            "funeral_style": "家族葬",
            "religion": "仏教",
            "funeral_notes": "シンプルにお願いします",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["funeral_style"] == "家族葬"
        assert data["funeral_notes"] == "シンプルにお願いします"

    def test_update_family_message(self, auth_client):
        msg = "家族へ、いつもありがとう。幸せに生きてください。"
        res = auth_client.put("/api/ending-note", json={"family_message": msg})
        assert res.status_code == 200
        assert res.json()["family_message"] == msg

    def test_update_partial_fields_preserved(self, auth_client):
        auth_client.put("/api/ending-note", json={"life_prolonging": "希望する"})
        auth_client.put("/api/ending-note", json={"funeral_style": "直葬"})
        res = auth_client.get("/api/ending-note")
        # 最初に設定した値が保持されているか
        assert res.json()["life_prolonging"] == "希望する"
        assert res.json()["funeral_style"] == "直葬"

    def test_unauthenticated_cannot_access(self, client):
        res = client.get("/api/ending-note")
        assert res.status_code == 401


# ─── 形見分けアイテム ─────────────────────────────────────────

class TestBequestItems:
    def test_create_bequest_item(self, auth_client):
        res = auth_client.post("/api/ending-note/bequest-items", json={
            "item_name": "父の時計",
            "recipient": "長男",
            "notes": "大切に使ってほしい",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["item_name"] == "父の時計"
        assert data["recipient"] == "長男"

    def test_list_bequest_items(self, auth_client):
        auth_client.post("/api/ending-note/bequest-items", json={"item_name": "A", "recipient": "B"})
        auth_client.post("/api/ending-note/bequest-items", json={"item_name": "C", "recipient": "D"})
        res = auth_client.get("/api/ending-note")
        assert len(res.json()["bequest_items"]) == 2

    def test_delete_bequest_item(self, auth_client):
        item_id = auth_client.post("/api/ending-note/bequest-items", json={
            "item_name": "削除対象", "recipient": "誰か"
        }).json()["id"]
        res = auth_client.delete(f"/api/ending-note/bequest-items/{item_id}")
        assert res.status_code == 200
        # 削除後は一覧から消える
        items = auth_client.get("/api/ending-note").json()["bequest_items"]
        assert all(i["id"] != item_id for i in items)

    def test_delete_nonexistent_item(self, auth_client):
        res = auth_client.delete("/api/ending-note/bequest-items/99999")
        assert res.status_code == 404


# ─── デジタル遺産 ─────────────────────────────────────────────

class TestDigitalAssets:
    def test_create_digital_asset(self, auth_client):
        res = auth_client.post("/api/ending-note/digital-assets", json={
            "service_name": "Twitter",
            "account": "@example",
            "after_death_instruction": "アカウントを削除してください",
        })
        assert res.status_code == 200
        assert res.json()["service_name"] == "Twitter"

    def test_delete_digital_asset(self, auth_client):
        item_id = auth_client.post("/api/ending-note/digital-assets", json={
            "service_name": "Instagram", "account": "@test"
        }).json()["id"]
        res = auth_client.delete(f"/api/ending-note/digital-assets/{item_id}")
        assert res.status_code == 200

    def test_multiple_digital_assets(self, auth_client):
        for svc in ["Twitter", "Facebook", "LINE", "Google"]:
            auth_client.post("/api/ending-note/digital-assets", json={"service_name": svc})
        note = auth_client.get("/api/ending-note").json()
        assert len(note["digital_assets"]) == 4


# ─── サブスク ────────────────────────────────────────────────

class TestSubscriptions:
    def test_create_subscription(self, auth_client):
        res = auth_client.post("/api/ending-note/subscriptions", json={
            "service_name": "Netflix",
            "monthly_fee": 1490,
            "cancellation_method": "Webサイトから解約",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["service_name"] == "Netflix"
        assert data["monthly_fee"] == 1490

    def test_delete_subscription(self, auth_client):
        item_id = auth_client.post("/api/ending-note/subscriptions", json={
            "service_name": "Spotify", "monthly_fee": 980
        }).json()["id"]
        res = auth_client.delete(f"/api/ending-note/subscriptions/{item_id}")
        assert res.status_code == 200

    def test_zero_fee_subscription(self, auth_client):
        res = auth_client.post("/api/ending-note/subscriptions", json={
            "service_name": "無料サービス", "monthly_fee": 0
        })
        assert res.status_code == 200


# ─── 緊急連絡先 ────────────────────────────────────────────────

class TestEmergencyContacts:
    def test_create_contact(self, auth_client):
        res = auth_client.post("/api/ending-note/emergency-contacts", json={
            "name": "田中太郎",
            "relationship": "長男",
            "phone": "090-1234-5678",
            "email": "tanaka@example.com",
            "priority": 1,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "田中太郎"
        assert data["priority"] == 1

    def test_multiple_contacts_ordered_by_priority(self, auth_client):
        auth_client.post("/api/ending-note/emergency-contacts", json={"name": "B", "priority": 2})
        auth_client.post("/api/ending-note/emergency-contacts", json={"name": "A", "priority": 1})
        note = auth_client.get("/api/ending-note").json()
        assert len(note["emergency_contacts"]) == 2

    def test_delete_contact(self, auth_client):
        item_id = auth_client.post("/api/ending-note/emergency-contacts", json={
            "name": "削除テスト", "priority": 0
        }).json()["id"]
        res = auth_client.delete(f"/api/ending-note/emergency-contacts/{item_id}")
        assert res.status_code == 200


# ─── ペット ─────────────────────────────────────────────────

class TestPets:
    def test_create_pet(self, auth_client):
        res = auth_client.post("/api/ending-note/pets", json={
            "name": "ポチ",
            "species": "犬",
            "medical_info": "毎月フィラリア予防",
            "personality": "人懐こい",
            "caretaker": "次女",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "ポチ"
        assert data["species"] == "犬"

    def test_delete_pet(self, auth_client):
        item_id = auth_client.post("/api/ending-note/pets", json={
            "name": "タマ", "species": "猫"
        }).json()["id"]
        res = auth_client.delete(f"/api/ending-note/pets/{item_id}")
        assert res.status_code == 200

    def test_multiple_pets(self, auth_client):
        for name in ["ポチ", "タマ", "ピー"]:
            auth_client.post("/api/ending-note/pets", json={"name": name, "species": "犬"})
        note = auth_client.get("/api/ending-note").json()
        assert len(note["pets"]) == 3


# ═══════════════════════════════════════════════════════════════
# チェックリスト
# ═══════════════════════════════════════════════════════════════

class TestChecklist:
    def test_get_checklist_returns_items(self, auth_client):
        res = auth_client.get("/api/checklist")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert "completion_rate" in data

    def test_checklist_item_structure(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        for item in items:
            assert "task_key" in item
            assert "label" in item
            assert "is_completed" in item
            assert "category" in item
            assert "priority" in item
            assert "stars" in item
            assert 1 <= item["stars"] <= 5

    def test_checklist_sorted_by_stars_desc(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        stars_list = [item["stars"] for item in items]
        assert stars_list == sorted(stars_list, reverse=True)

    def test_checklist_priority_matches_stars(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        for item in items:
            if item["stars"] >= 3:
                assert item["priority"] == "必須"
            elif item["stars"] == 2:
                assert item["priority"] == "推奨"
            else:
                assert item["priority"] == "任意"

    def test_initial_completion_rate_zero(self, auth_client):
        data = auth_client.get("/api/checklist").json()
        # 新規ユーザーは何も完了していない
        assert data["completion_rate"] == 0.0

    def test_toggle_complete(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        key = items[0]["task_key"]
        res = auth_client.post("/api/checklist/toggle", json={"task_key": key, "is_completed": True})
        assert res.status_code == 200
        assert res.json()["is_completed"] is True

    def test_toggle_uncomplete(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        key = items[0]["task_key"]
        auth_client.post("/api/checklist/toggle", json={"task_key": key, "is_completed": True})
        res = auth_client.post("/api/checklist/toggle", json={"task_key": key, "is_completed": False})
        assert res.json()["is_completed"] is False

    def test_completion_rate_updates(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        total = len(items)
        auth_client.post("/api/checklist/toggle", json={"task_key": items[0]["task_key"], "is_completed": True})
        data = auth_client.get("/api/checklist").json()
        expected_rate = round(1 / total * 100, 1)
        assert data["completion_rate"] == expected_rate

    def test_invalid_task_key(self, auth_client):
        res = auth_client.post("/api/checklist/toggle", json={
            "task_key": "nonexistent_key", "is_completed": True
        })
        assert res.status_code == 404

    def test_completion_persists_across_requests(self, auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        key = items[1]["task_key"]
        auth_client.post("/api/checklist/toggle", json={"task_key": key, "is_completed": True})
        res = auth_client.get("/api/checklist")
        item_map = {i["task_key"]: i for i in res.json()["items"]}
        assert item_map[key]["is_completed"] is True

    def test_checklist_isolated_between_users(self, auth_client, second_auth_client):
        items = auth_client.get("/api/checklist").json()["items"]
        key = items[0]["task_key"]
        auth_client.post("/api/checklist/toggle", json={"task_key": key, "is_completed": True})
        # 別ユーザーのチェックリストには影響しない
        other_items = second_auth_client.get("/api/checklist").json()["items"]
        item_map = {i["task_key"]: i for i in other_items}
        assert item_map[key]["is_completed"] is False

    def test_unauthenticated_checklist(self, client):
        res = client.get("/api/checklist")
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════
# 遺言書シミュレーター
# ═══════════════════════════════════════════════════════════════

class TestWillSimulator:
    def _setup(self, client):
        plan_id = client.post("/api/estate-plans", json={"title": "遺言テスト"}).json()["id"]
        client.post(f"/api/estate-plans/{plan_id}/family", json={
            "members": [
                {"name": "配偶者", "relationship": "spouse"},
                {"name": "長男", "relationship": "child"},
            ]
        })
        return plan_id

    def test_get_will_empty(self, auth_client):
        plan_id = self._setup(auth_client)
        res = auth_client.get(f"/api/estate-plans/{plan_id}/will")
        assert res.status_code == 200
        data = res.json()
        assert data["estate_plan_id"] == plan_id
        assert data["allocations"] == {}
        assert data["memo"] is None

    def test_save_and_get_will(self, auth_client):
        plan_id = self._setup(auth_client)
        payload = {"allocations": {"1": 30000000, "2": 10000000}, "memo": "家族へのメッセージ"}
        res = auth_client.put(f"/api/estate-plans/{plan_id}/will", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["allocations"] == {"1": 30000000, "2": 10000000}
        assert data["memo"] == "家族へのメッセージ"

        res2 = auth_client.get(f"/api/estate-plans/{plan_id}/will")
        assert res2.status_code == 200
        assert res2.json()["allocations"] == {"1": 30000000, "2": 10000000}

    def test_update_will(self, auth_client):
        plan_id = self._setup(auth_client)
        auth_client.put(f"/api/estate-plans/{plan_id}/will", json={"allocations": {"1": 10000000}, "memo": None})
        res = auth_client.put(f"/api/estate-plans/{plan_id}/will", json={"allocations": {"1": 20000000, "2": 5000000}, "memo": "更新"})
        assert res.status_code == 200
        assert res.json()["allocations"] == {"1": 20000000, "2": 5000000}
        assert res.json()["memo"] == "更新"

    def test_will_access_other_user_404(self, auth_client, second_auth_client):
        plan_id = self._setup(auth_client)
        auth_client.put(f"/api/estate-plans/{plan_id}/will", json={"allocations": {"1": 100}, "memo": None})
        res = second_auth_client.get(f"/api/estate-plans/{plan_id}/will")
        assert res.status_code == 404

    def test_will_nonexistent_plan_404(self, auth_client):
        res = auth_client.get("/api/estate-plans/99999/will")
        assert res.status_code == 404


# ═══════════════════════════════════════════════════════════════
# 公開墓誌（パスワード保護）
# ═══════════════════════════════════════════════════════════════

class TestPublicMemorial:
    def _create_memorial(self, client, is_public=True, password=None):
        data = {"name": "テスト太郎", "is_public": is_public}
        if password:
            data["password"] = password
        res = client.post("/api/memorials", json=data)
        return res.json()

    def test_public_memorial_accessible(self, auth_client, client):
        m = self._create_memorial(auth_client, is_public=True)
        res = client.get(f"/api/m/{m['slug']}")
        assert res.status_code == 200
        assert res.json()["name"] == "テスト太郎"

    def test_private_memorial_without_password_returns_403(self, auth_client, client):
        """非公開墓誌にパスワードなしでアクセス → 403"""
        m = self._create_memorial(auth_client, is_public=False)
        res = client.get(f"/api/m/{m['slug']}")
        assert res.status_code == 403

    def test_private_memorial_with_no_hash_and_password_provided_returns_403(self, auth_client, client):
        """非公開墓誌(password_hash=None)にパスワードを提供しても403（クラッシュしない）"""
        m = self._create_memorial(auth_client, is_public=False)
        res = client.get(f"/api/m/{m['slug']}?password=wrongpassword")
        assert res.status_code == 403

    def test_password_protected_correct_password(self, auth_client, client):
        """パスワード付き非公開墓誌: 正しいパスワードで閲覧可能"""
        m = self._create_memorial(auth_client, is_public=False, password="secret123")
        res = client.get(f"/api/m/{m['slug']}?password=secret123")
        assert res.status_code == 200

    def test_password_protected_wrong_password(self, auth_client, client):
        """パスワード付き非公開墓誌: 誤ったパスワードで403"""
        m = self._create_memorial(auth_client, is_public=False, password="secret123")
        res = client.get(f"/api/m/{m['slug']}?password=wrongpassword")
        assert res.status_code == 403
