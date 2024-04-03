from orjson import orjson
from aiogram import Router
from aiogram.filters import Text
from aiogram.types import Message

router = Router()


@router.message(Text(text='Очистить очередь', ignore_case=True))
async def status(message: Message):
    """

    :param message:
    """
    if message.from_user.username == 'Endresk':
        try:
            with open('json_files/AutoCrossing.json', "rb") as read_file:
                AutoCrossingJson = orjson.loads(read_file.read())
        except:
            with open('json_files/AutoCrossing.json', 'w'):
                pass
        if AutoCrossingJson:

            json_data = orjson.dumps({})
            with open('json_files/AutoCrossing.json', 'wb') as f:
                f.write(json_data)
            await message.answer("Очередь очищена!")
        else:
            await message.answer("Очередь не очищена! Является пустой!")
