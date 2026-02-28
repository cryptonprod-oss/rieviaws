from __future__ import annotations

from datetime import datetime
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Settings
from db import ReviewLogRecord, get_last_order, increment_and_get_order, save_review
from keyboards import confirm_keyboard, edit_keyboard, main_menu_keyboard, rating_keyboard
from states import ReviewFSM

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


def build_template(data: dict, order_no: str) -> str:
    stars = "⭐" * int(data["rating"])
    return (
        "📝 Обратная связь\n"
        f"👤 Юзернейм: {data['username']}\n"
        f"🕒 Дата платежа: {data['payment_date']}\n"
        f"🔢 Номер заказа: {order_no}\n"
        f"📄 Отзыв: {data['review_text']}\n"
        f"Оценка: {stars}"
    )


def is_valid_date(date_text: str) -> bool:
    try:
        dt = datetime.strptime(date_text, "%d.%m.%Y")
        return dt.strftime("%d.%m.%Y") == date_text
    except ValueError:
        return False


async def ensure_access(message: Message, settings: Settings) -> bool:
    user = message.from_user
    if not user or not is_admin(user.id, settings):
        await message.answer("Нет доступа")
        return False
    return True


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext, settings: Settings) -> None:
    if not await ensure_access(message, settings):
        return
    await state.clear()
    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext, settings: Settings) -> None:
    if not await ensure_access(message, settings):
        return
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Сейчас нечего отменять.", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Создание отзыва отменено.", reply_markup=main_menu_keyboard())


@router.message(Command("new"))
@router.message(F.text == "➕ Создать отзыв")
async def new_handler(message: Message, state: FSMContext, settings: Settings) -> None:
    if not await ensure_access(message, settings):
        return
    await state.clear()
    await state.set_state(ReviewFSM.username)
    await message.answer("Введите юзернейм (можно с @):")


@router.message(F.text == "📌 Последний номер")
async def last_number_handler(message: Message, settings: Settings, db_path: str) -> None:
    if not await ensure_access(message, settings):
        return
    last_order = await get_last_order(db_path)
    await message.answer(f"Последний подтвержденный номер: {last_order:05d}")


@router.message(ReviewFSM.username)
async def username_step(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Юзернейм не должен быть пустым. Введите снова:")
        return

    await state.update_data(username=text)
    await state.set_state(ReviewFSM.payment_date)
    await message.answer("Введите дату платежа в формате DD.MM.YYYY:")


@router.message(ReviewFSM.payment_date)
async def payment_date_step(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not is_valid_date(text):
        await message.answer("Некорректная дата. Пример: 25.12.2025")
        return

    await state.update_data(payment_date=text)
    await state.set_state(ReviewFSM.review_text)
    await message.answer("Введите текст отзыва (до 800 символов):")


@router.message(ReviewFSM.review_text)
async def review_text_step(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Текст отзыва не должен быть пустым. Введите снова:")
        return
    if len(text) > 800:
        await message.answer("Слишком длинный отзыв. Максимум 800 символов.")
        return

    await state.update_data(review_text=text)
    await state.set_state(ReviewFSM.rating)
    await message.answer("Выберите оценку:", reply_markup=rating_keyboard().as_markup())


@router.callback_query(ReviewFSM.rating, F.data.startswith("rating:"))
async def rating_step(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    rating = int(value)
    if rating < 1 or rating > 5:
        await callback.answer("Некорректная оценка", show_alert=True)
        return

    await state.update_data(rating=rating)
    await state.set_state(ReviewFSM.confirm)
    data = await state.get_data()
    preview = build_template(data, order_no="<00001>")
    await callback.message.edit_text(
        f"Проверьте данные:\n\n{preview}",
        reply_markup=confirm_keyboard().as_markup(),
    )
    await callback.answer()


@router.callback_query(ReviewFSM.confirm, F.data == "confirm:cancel")
async def confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Создание отзыва отменено.")
    await callback.message.answer("Возврат в меню.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(ReviewFSM.confirm, F.data == "confirm:edit")
async def confirm_edit(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Что изменить?",
        reply_markup=edit_keyboard().as_markup(),
    )
    await callback.answer()


@router.callback_query(ReviewFSM.confirm, F.data == "confirm:ok")
async def confirm_ok(
    callback: CallbackQuery,
    state: FSMContext,
    settings: Settings,
    db_path: str,
) -> None:
    data = await state.get_data()
    order_no = await increment_and_get_order(db_path)
    final_text = build_template(data, order_no)

    user = callback.from_user
    await save_review(
        db_path,
        ReviewLogRecord(
            admin_user_id=user.id,
            username=data["username"],
            pay_date=data["payment_date"],
            order_no=order_no,
            rating=int(data["rating"]),
            review_text=data["review_text"],
        ),
        settings.timezone,
    )

    await state.clear()
    await callback.message.edit_text(final_text)
    await callback.message.answer("Готово. Вы можете создать новый отзыв.", reply_markup=main_menu_keyboard())
    await callback.answer("Сохранено")


@router.callback_query(ReviewFSM.confirm, F.data.startswith("edit:"))
async def edit_fields(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":", 1)[1]

    if action == "back":
        data = await state.get_data()
        preview = build_template(data, order_no="<00001>")
        await callback.message.edit_text(
            f"Проверьте данные:\n\n{preview}",
            reply_markup=confirm_keyboard().as_markup(),
        )
        await callback.answer()
        return

    mapping = {
        "username": (ReviewFSM.username, "Введите новый юзернейм:"),
        "payment_date": (ReviewFSM.payment_date, "Введите новую дату DD.MM.YYYY:"),
        "review_text": (ReviewFSM.review_text, "Введите новый текст отзыва (до 800 символов):"),
        "rating": (ReviewFSM.rating, "Выберите новую оценку:"),
    }

    if action not in mapping:
        await callback.answer("Неизвестный пункт", show_alert=True)
        return

    target_state, prompt = mapping[action]
    await state.set_state(target_state)

    if target_state == ReviewFSM.rating:
        await callback.message.edit_text(prompt, reply_markup=rating_keyboard().as_markup())
    else:
        await callback.message.edit_text(prompt)

    await callback.answer()


@router.message()
async def fallback(message: Message, settings: Settings) -> None:
    if not await ensure_access(message, settings):
        return
    await message.answer(
        "Не понял команду. Используйте /start, /new или /cancel.",
        reply_markup=main_menu_keyboard(),
    )
    logger.info("Unhandled message from %s: %s", message.from_user.id if message.from_user else "?", message.text)
