from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать отзыв")],
            [KeyboardButton(text="📌 Последний номер")],
        ],
        resize_keyboard=True,
    )


def rating_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for value in range(1, 6):
        stars = "⭐" * value
        builder.button(text=stars, callback_data=f"rating:{value}")
    builder.adjust(1)
    return builder


def confirm_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm:ok")
    builder.button(text="✏️ Изменить", callback_data="confirm:edit")
    builder.button(text="❌ Отмена", callback_data="confirm:cancel")
    builder.adjust(1)
    return builder


def edit_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Юзернейм", callback_data="edit:username")
    builder.button(text="Дата", callback_data="edit:payment_date")
    builder.button(text="Отзыв", callback_data="edit:review_text")
    builder.button(text="Оценка", callback_data="edit:rating")
    builder.button(text="⬅️ Назад", callback_data="edit:back")
    builder.adjust(2, 2, 1)
    return builder
