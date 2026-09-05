"""
Cover for generated passwords.

Generated passwords are handed to new users, so the guarantees the docstring
makes about length and character mix have to hold on every draw, not on average.
"""

import string

import pytest

from app.shared.utils.password_generator import generate_secure_password

SPECIAL = "!@#$%^&*"
DRAWS = 200


class TestLength:
    def test_default_length(self) -> None:
        assert len(generate_secure_password()) == 16

    @pytest.mark.parametrize("length", [12, 13, 20, 64, 128])
    def test_requested_length_is_honoured(self, length: int) -> None:
        assert len(generate_secure_password(length)) == length

    @pytest.mark.parametrize("length", [11, 8, 4, 1, 0, -1])
    def test_lengths_below_the_floor_are_refused(self, length: int) -> None:
        with pytest.raises(ValueError, match="at least 12 characters"):
            generate_secure_password(length)


class TestCharacterMix:
    @pytest.mark.parametrize("length", [12, 16, 32])
    def test_every_class_is_present(self, length: int) -> None:
        for _ in range(DRAWS):
            password = generate_secure_password(length)
            assert any(c in string.ascii_uppercase for c in password)
            assert any(c in string.ascii_lowercase for c in password)
            assert any(c in string.digits for c in password)
            assert any(c in SPECIAL for c in password)

    def test_no_character_outside_the_documented_alphabet(self) -> None:
        allowed = set(string.ascii_letters + string.digits + SPECIAL)
        for _ in range(DRAWS):
            assert set(generate_secure_password()) <= allowed


class TestRandomness:
    def test_successive_draws_differ(self) -> None:
        """A repeat at 16 characters would mean the generator is not random."""
        drawn = {generate_secure_password() for _ in range(DRAWS)}
        assert len(drawn) == DRAWS

    def test_the_guaranteed_classes_are_not_pinned_to_the_first_positions(self) -> None:
        """The shuffle has to move the four seeded characters around."""
        first_chars = {generate_secure_password()[0] for _ in range(DRAWS)}
        classes = {
            "upper": any(c in string.ascii_uppercase for c in first_chars),
            "lower": any(c in string.ascii_lowercase for c in first_chars),
            "digit": any(c in string.digits for c in first_chars),
        }
        assert sum(classes.values()) >= 2
