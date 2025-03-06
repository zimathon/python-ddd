from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """金額を表す値オブジェクト"""
    amount: Decimal

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

    @classmethod
    def of(cls, amount) -> 'Money':
        return cls(Decimal(str(amount)))

    def is_positive_or_zero(self) -> bool:
        return self.amount >= 0

    def negate(self) -> 'Money':
        return Money(-self.amount)

    @staticmethod
    def add(a: 'Money', b: 'Money') -> 'Money':
        return Money(a.amount + b.amount)

    @staticmethod
    def subtract(a: 'Money', b: 'Money') -> 'Money':
        return Money(a.amount - b.amount)


# ゼロ円を表す定数
ZERO = Money(Decimal('0')) 