import json
from decimal import Decimal
from time import sleep

from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from orjson import orjson
from tabulate import tabulate

from settings import TOKEN, ListCouple, MainInterval, FileDataList, CoupleResult
from general.graph_couple import Graph_couple
from aiogram import Router, types
from aiogram.types import Message, BufferedInputFile
from aiogram.utils.markdown import hpre, text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboard.keyboard_coin import coin_keyboard
from keyboard.keyboard_update import Graph_Update_keyboard
from general.other import ListEveryTabulate

router = Router()

Interval = int(int(MainInterval) / 60)


class Form_add(StatesGroup):
    one = State()
    two = State()
    message_id = State()


@router.message(Text(text='Графики', ignore_case=True))
async def stat_couples_graph(message: Message):
    if message.from_user.username == 'Endresk':
        buttons = [
            [
                types.InlineKeyboardButton(text='Мои пары', callback_data="graph_CoupleAllMy"),
                types.InlineKeyboardButton(text='Одна пара', callback_data="graph_CoupleOne"),
                types.InlineKeyboardButton(text=f'{Interval}ч', callback_data="graph_CoupleAll-One")
            ]
            # [
            #     types.InlineKeyboardButton(text=f'График символа', callback_data="graph_Symbol")
            # ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer('Выберите вариант: ', reply_markup=keyboard)


async def Pagination(state):
    builder = InlineKeyboardBuilder()

    data = await state.get_data()

    page = int(data['page'])
    DictIndex = data['Dict']

    for i in DictIndex[page]:
        builder.add(types.InlineKeyboardButton(
            text=i,
            callback_data=f"oneGraph_{i}"))

    if page != 0 and int(next(reversed(DictIndex.keys()))) != page:
        builder.row(types.InlineKeyboardButton(text='Назад', callback_data='back'))
        builder.add(types.InlineKeyboardButton(text='Далее', callback_data='next'))
        builder.adjust(4)
    elif page == 0:
        builder.row(types.InlineKeyboardButton(text='Далее', callback_data='next'))
        builder.adjust(4)
    else:
        builder.adjust(4)
        builder.row(types.InlineKeyboardButton(text='Назад', callback_data='back'))

    return builder.as_markup()


@router.callback_query(Text(startswith="next"))
async def callbacks_next(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(page=int(data['page']) + 60)
    await callback.message.edit_text("Выберите бренд", reply_markup=await Pagination(state))
    await callback.answer()


@router.callback_query(Text(startswith="back"))
async def callbacks_back(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(page=int(data['page']) - 60)
    await callback.message.edit_text("Выберите бренд", reply_markup=await Pagination(state))
    await callback.answer()


@router.callback_query(Text(startswith="graph_"))
async def callbacks_graph(callback: types.CallbackQuery, state: FSMContext):
    teg = callback.data.split("_")[-1]

    with open(f'json_files/{ListCouple}.json', 'r') as f:
        JsonListSymbols = orjson.loads(f.read())

    if teg == 'CoupleOne':
        with open(CoupleResult, 'rb') as f:
            DictResult = orjson.loads(f.read())

        ListOneCoin = []

        for key in DictResult['result'].keys():

            if f'{key.split("_")[0]}' not in ListOneCoin:
                ListOneCoin.append(key.split("_")[0])

        DictResult = list(sorted(ListOneCoin))
        LenDict = len(DictResult)

        DictIndex = {}
        for i in range(0, LenDict, 60):
            DictIndex[i] = DictResult[i:i + 60]

        await state.update_data(page=0)
        await state.update_data(Dict=DictIndex)

        await callback.message.edit_text('Выберите первый коин',
                                         parse_mode="HTML",
                                         reply_markup=await Pagination(state))
    elif teg == 'CoupleAllMy':

        with open('json_files/DataCouples.json', "rb") as read_file:
            DataCouples = orjson.loads(read_file.read())

        if DataCouples:
            await callback.message.edit_text('Вы выбрали "Мои пары"')

            for i in DataCouples.values():
                one = i["ONE"].split("USDT")[0]
                two = i["TWO"].split("USDT")[0]

                with open(FileDataList, 'rb') as f:
                    DataList = orjson.loads(f.read())

                ValueCouple = DataList[f'{one}_{two}']

                ListEvery, plot_file, _, _ = ListEveryTabulate(
                    one, two, ValueCouple)

                await callback.message.answer_photo(BufferedInputFile(plot_file.getvalue(),
                                                                      f'{i["ONE"]}_{i["TWO"]}.png'),
                                                    caption=f'{hpre(ListEvery)}',
                                                    parse_mode="HTML")

        else:
            await callback.message.edit_text('У вас нет пар на данный момент!')

    elif teg.split("-")[0] == 'CoupleAll':

        await callback.message.edit_text(f'Вы выбрали "{Interval}ч"')

        with open(CoupleResult, 'r') as f:
            result = json.load(f)

        for key, values in result['result'].items():
            PValue, ZScore = Decimal('{:.3f}'.format(values[0])), Decimal('{:.3f}'.format(values[2]))

            OneCoin = key.split("_")[0]
            TwoCoin = key.split("_")[1]

            plot_file, _, _, stockOne, stockTwo = Graph_couple(OneCoin, TwoCoin).load(JsonListSymbols)

            data = tabulate([[OneCoin, TwoCoin],
                             ['PValue', PValue],
                             ['ZScore', ZScore]],
                            tablefmt='simple',
                            showindex=False,
                            colalign=("right", "left"))

            await callback.message.answer_photo(
                BufferedInputFile(plot_file.getvalue(), f'{OneCoin}_{TwoCoin}.png'),
                caption=text(hpre(data)),
                parse_mode="HTML")

    try:
        await callback.answer(cache_time=30)
    except:
        pass


async def graph(callback, one, two):
    with open(FileDataList, 'rb') as f:
        DataList = orjson.loads(f.read())

    ValueCouple = DataList[f'{one}_{two}']

    ListEvery, plot_file, _, _ = ListEveryTabulate(
        one, two, ValueCouple)

    await callback.message.answer_photo(
        BufferedInputFile(plot_file.getvalue(), f'{one}_{two}.png'),
        caption=f'{hpre(ListEvery)}',
        parse_mode="HTML",
        reply_markup=Graph_Update_keyboard())


@router.callback_query(Text(startswith="oneGraph_"))
async def callbacks_one_graph(callback: types.CallbackQuery):
    one_symbol = callback.data.replace('oneGraph_', '')

    await callback.message.edit_text('Выберите второй коин', reply_markup=coin_keyboard("couple_graph", one_symbol))
    await callback.answer()


@router.callback_query(Text(startswith="couple_graph_"))
async def callbacks_add(callback: types.CallbackQuery, state: FSMContext):
    symbols = callback.data.split("_")[-1]
    one = symbols.split("-")[0]
    two = symbols.split("-")[1]
    await state.update_data(one=one)
    await state.update_data(two=two)

    await callback.message.delete()
    await graph(callback, one, two)
    await state.update_data(message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(Text(startswith="GraphUpdate"))
async def callbacks_update(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    one = data['one']
    two = data['two']

    await callback.message.delete()
    await graph(callback, one, two)
    await callback.answer()
