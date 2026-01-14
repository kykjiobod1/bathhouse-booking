"""
Инициализация конфигурации системы.
Создает дефолтные значения в SystemConfig при первом запуске.
"""
import logging
from bathhouse_booking.bookings.models import SystemConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIGS = [
    {
        'key': 'PAYMENT_INSTRUCTION',
        'value': 'Пожалуйста, переведите оплату на карту •1234 5678 9012 3456• и нажмите "Я оплатил"',
        'description': 'Инструкция по оплате для клиентов'
    },
    {
        'key': 'OPEN_HOUR',
        'value': '9',
        'description': 'Час открытия (0-23)'
    },
    {
        'key': 'CLOSE_HOUR',
        'value': '22',
        'description': 'Час закрытия (0-23)'
    },
    {
        'key': 'SLOT_STEP_MINUTES',
        'value': '30',
        'description': 'Шаг между слотами в минутах'
    },
    {
        'key': 'MIN_BOOKING_MINUTES',
        'value': '120',
        'description': 'Минимальная продолжительность бронирования в минутах'
    },
    {
        'key': 'MAX_ACTIVE_BOOKINGS_PER_CLIENT',
        'value': '3',
        'description': 'Максимальное количество активных бронирований на одного клиента'
    },
    {
        'key': 'BOOKING_SESSION_TIMEOUT_MINUTES',
        'value': '30',
        'description': 'Таймаут сессии бронирования в минутах'
    },
    {
        'key': 'TELEGRAM_NOTIFICATIONS_ENABLED',
        'value': 'true',
        'description': 'Включены ли уведомления в Telegram'
    }
]

def initialize_system_config():
    """Инициализировать системную конфигурацию дефолтными значениями"""
    created_count = 0
    updated_count = 0
    
    for config_data in DEFAULT_CONFIGS:
        key = config_data['key']
        value = config_data['value']
        description = config_data['description']
        
        try:
            config, created = SystemConfig.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'description': description
                }
            )
            
            if created:
                created_count += 1
                logger.info(f"Created config: {key} = {value}")
            else:
                # Обновляем описание, если оно изменилось
                if config.description != description:
                    config.description = description
                    config.save()
                    updated_count += 1
                    logger.info(f"Updated description for config: {key}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize config {key}: {e}")
    
    logger.info(f"System config initialized: {created_count} created, {updated_count} updated")
    return created_count + updated_count


async def initialize_system_config_async():
    """Асинхронная версия инициализации системной конфигурации"""
    from asgiref.sync import sync_to_async
    return await sync_to_async(initialize_system_config)()


def get_config(key, default=None):
    """Получить значение конфигурации как строку"""
    try:
        config = SystemConfig.objects.get(key=key)
        return config.value
    except SystemConfig.DoesNotExist:
        logger.warning(f"Config {key} not found, using default: {default}")
        return default


def get_config_int(key, default=0):
    """Получить значение конфигурации как целое число"""
    try:
        config = SystemConfig.objects.get(key=key)
        return int(config.value)
    except SystemConfig.DoesNotExist:
        logger.warning(f"Config {key} not found, using default: {default}")
        return default
    except ValueError as e:
        logger.error(f"Failed to cast config {key} value to int: {e}")
        return default


async def get_config_int_async(key, default=0):
    """Асинхронная версия get_config_int"""
    from asgiref.sync import sync_to_async
    return await sync_to_async(get_config_int)(key, default)


def get_config_bool(key, default=False):
    """Получить значение конфигурации как булево значение"""
    try:
        config = SystemConfig.objects.get(key=key)
        value = config.value.lower()
        return value in ('true', '1', 'yes', 'y', 'on')
    except SystemConfig.DoesNotExist:
        logger.warning(f"Config {key} not found, using default: {default}")
        return default


# Инициализация должна быть вызвана вручную после настройки Django
# initialize_system_config()