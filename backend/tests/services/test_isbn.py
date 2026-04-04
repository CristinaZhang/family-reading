from __future__ import annotations

import pytest
from app.services.isbn import normalize_isbn, is_valid_isbn10, is_valid_isbn13, to_isbn13


def test_normalize_isbn():
    """测试ISBN标准化函数"""
    # 测试正常ISBN
    assert normalize_isbn("9787544270878") == "9787544270878"
    # 测试带有连字符的ISBN
    assert normalize_isbn("978-7-5442-7087-8") == "9787544270878"
    # 测试带有空格的ISBN
    assert normalize_isbn("978 7 5442 7087 8") == "9787544270878"
    # 测试小写X的ISBN
    assert normalize_isbn("0306406152x") == "0306406152X"
    # 测试空字符串
    assert normalize_isbn("") == ""
    # 测试None
    assert normalize_isbn(None) == ""


def test_is_valid_isbn10():
    """测试ISBN-10验证函数"""
    # 测试有效的ISBN-10（使用已知有效的ISBN）
    assert is_valid_isbn10("0306406152") is True  # 已知有效的ISBN-10
    assert is_valid_isbn10("0140449116") is True  # 已知有效的ISBN-10
    # 测试带X的ISBN-10
    assert is_valid_isbn10("080442957X") is True  # 已知有效的带X的ISBN-10
    # 测试无效的ISBN-10
    assert is_valid_isbn10("1234567890") is False  # 校验位错误
    assert is_valid_isbn10("123456789") is False  # 长度错误
    assert is_valid_isbn10("12345678901") is False  # 长度错误
    assert is_valid_isbn10("123456789A") is False  # 包含无效字符


def test_is_valid_isbn13():
    """测试ISBN-13验证函数"""
    # 测试有效的ISBN-13
    assert is_valid_isbn13("9787544270878") is True  # 已知有效的ISBN-13
    assert is_valid_isbn13("9780306406157") is True  # 已知有效的ISBN-13
    # 测试无效的ISBN-13
    assert is_valid_isbn13("9787544270870") is False  # 校验位错误
    assert is_valid_isbn13("978754427087") is False  # 长度错误
    assert is_valid_isbn13("97875442708789") is False  # 长度错误
    assert is_valid_isbn13("978754427087X") is False  # 包含无效字符


def test_to_isbn13():
    """测试ISBN转换为ISBN-13函数"""
    # 测试已经是ISBN-13的情况
    assert to_isbn13("9787544270878") == "9787544270878"
    # 测试ISBN-10转换为ISBN-13（使用已知有效的ISBN-10）
    isbn10 = "0306406152"
    isbn13_result = to_isbn13(isbn10)
    assert len(isbn13_result) == 13
    assert isbn13_result.startswith("978")
    # 测试带有连字符的ISBN-10
    assert to_isbn13("0-306-40615-2") == isbn13_result
    # 测试无效的ISBN
    with pytest.raises(ValueError, match="Invalid ISBN"):
        to_isbn13("1234567890")  # 无效的ISBN-10
    with pytest.raises(ValueError, match="Invalid ISBN"):
        to_isbn13("123456789")  # 长度错误的ISBN
    with pytest.raises(ValueError, match="Invalid ISBN"):
        to_isbn13("1234567890123")  # 无效的ISBN-13