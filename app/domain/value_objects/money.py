import decimal
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount: decimal.Decimal
    currency: str

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount must be a positive number")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currencies must be the same")
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currencies must be the same")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: decimal.Decimal) -> "Money":
        return Money(self.amount * factor, self.currency)

    def divide(self, divisor: decimal.Decimal) -> "Money":
        if divisor == 0:
            raise ValueError("Division by zero")
        return Money(self.amount / divisor, self.currency)
