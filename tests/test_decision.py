# -*- coding: utf-8 -*-
"""判定邏輯（core/decision.py）單元測試"""

import pytest

from core.decision import (
    ClassSemantics, ClassificationPolicy, DefectPolicy, ObjectPolicy, build_policy,
)


# ---------------------------------------------------------------------- #
# ClassSemantics
# ---------------------------------------------------------------------- #

class TestClassSemantics:

    def test_explicit_declaration_wins(self):
        """設定檔顯式宣告優先於關鍵字識別"""
        s = ClassSemantics.resolve(
            {0: "foo", 1: "bar"},
            explicit_ok=["bar"], explicit_ng=["foo"],
        )
        assert s.source == "explicit"
        assert s.ok_classes == ["bar"]
        assert s.ng_classes == ["foo"]
        assert s.is_classification

    def test_keyword_fallback_english(self):
        s = ClassSemantics.resolve({0: "NG", 1: "OK"})
        assert s.source == "keyword"
        assert s.is_classification
        assert "OK" in s.ok_classes and "NG" in s.ng_classes

    def test_keyword_fallback_chinese(self):
        s = ClassSemantics.resolve({0: "不良", 1: "良品"})
        assert s.is_classification

    def test_ng_keyword_priority(self):
        """'abnormal' 含 'normal'，必須先比對 NG 關鍵字避免誤判為 OK"""
        s = ClassSemantics.resolve({0: "abnormal", 1: "normal"})
        assert "abnormal" in s.ng_classes
        assert "normal" in s.ok_classes

    def test_no_semantics_for_generic_classes(self):
        s = ClassSemantics.resolve({0: "person", 1: "car"})
        assert s.source == "none"
        assert not s.is_classification


# ---------------------------------------------------------------------- #
# ClassificationPolicy
# ---------------------------------------------------------------------- #

class TestClassificationPolicy:

    @pytest.fixture
    def policy(self):
        return ClassificationPolicy(
            ClassSemantics(ok_classes=["OK"], ng_classes=["NG"], source="explicit")
        )

    def test_ng_class_detected(self, policy):
        assert policy.judge(["NG"]).result == "NG"

    def test_ok_class_detected(self, policy):
        assert policy.judge(["OK"]).result == "OK"

    def test_ng_wins_over_ok(self, policy):
        """同時檢測到 OK 與 NG → NG 優先"""
        assert policy.judge(["OK", "NG"]).result == "NG"

    def test_nothing_detected_is_ng(self, policy):
        """分類模型沒檢測到任何類別 = 異常/缺失 → NG"""
        assert policy.judge([]).result == "NG"

    def test_unknown_class_is_ng(self, policy):
        """檢測到未宣告語意的類別 → 保守判 NG"""
        assert policy.judge(["mystery"]).result == "NG"

    def test_requires_classification_semantics(self):
        with pytest.raises(ValueError):
            ClassificationPolicy(ClassSemantics())


# ---------------------------------------------------------------------- #
# DefectPolicy
# ---------------------------------------------------------------------- #

class TestDefectPolicy:

    def test_no_detection_is_ok(self):
        assert DefectPolicy().judge([]).result == "OK"

    def test_any_detection_is_ng_without_whitelist(self):
        assert DefectPolicy().judge(["scratch"]).result == "NG"

    def test_ng_whitelist_hit(self):
        p = DefectPolicy(ng_classes=["crack"])
        assert p.judge(["crack"]).result == "NG"

    def test_ng_whitelist_miss_is_ok(self):
        p = DefectPolicy(ng_classes=["crack"])
        assert p.judge(["dust"]).result == "OK"


# ---------------------------------------------------------------------- #
# ObjectPolicy
# ---------------------------------------------------------------------- #

class TestObjectPolicy:

    def test_detection_is_ok(self):
        assert ObjectPolicy().judge(["product"]).result == "OK"

    def test_no_detection_is_ng(self):
        assert ObjectPolicy().judge([]).result == "NG"


# ---------------------------------------------------------------------- #
# build_policy
# ---------------------------------------------------------------------- #

class TestBuildPolicy:

    def test_auto_with_classification_semantics(self):
        s = ClassSemantics(ok_classes=["OK"], ng_classes=["NG"], source="keyword")
        assert isinstance(build_policy("auto", s), ClassificationPolicy)

    def test_auto_without_semantics_falls_back_to_defect(self):
        assert isinstance(build_policy("auto", ClassSemantics()), DefectPolicy)

    def test_object_mode(self):
        assert isinstance(build_policy("object", ClassSemantics()), ObjectPolicy)

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            build_policy("banana", ClassSemantics())
