from farmer.ext.prompt import NumberValidator, YesNoValidator, prompt_yes_no
from mock import patch
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from pytest import raises


def test_yesnovalidator_valid_y():
    validator = YesNoValidator()

    doc = Document("Y")
    validator.validate(doc)

    doc = Document("y")
    validator.validate(doc)


def test_yesnovalidator_valid_n():
    validator = YesNoValidator()

    doc = Document("N")
    validator.validate(doc)

    doc = Document("n")
    validator.validate(doc)


def test_yesnovalidator_invalid():
    validator = YesNoValidator()

    doc = Document("T")
    with raises(ValidationError):
        validator.validate(doc)

    doc = Document("a")
    with raises(ValidationError):
        validator.validate(doc)


def test_numbervalidator_valid():
    validator = NumberValidator()

    numbers = [3454, 1, 45, 23, 7, 8678]
    for num in numbers:
        doc = Document(str(num))
        validator.validate(doc)


def test_numbervalidator_invalid():
    validator = NumberValidator()

    numbers = ['a', 'hfg', 'sd']
    for num in numbers:
        doc = Document(str(num))
        with raises(ValidationError):
            validator.validate(doc)