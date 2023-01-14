from aiohttp import ClientSession
from skodaconnect import Connection

from core.config import COMPONENTS, is_enabled



async def init_session(email, password, print_response=False):
    session = ClientSession(headers={'Connection': 'keep-alive'})
    login_success = False
    print(f"Initiating new session to Skoda Connect using email {email}")
    try:
        connection = Connection(session, email, password, print_response)
        if not login_success:
            print("Attempting to login to the Skoda Connect service")
            login_success = await connection.doLogin()
    except Exception as e:
        print(f"Login failed: {e}")
        return None

    if login_success:
        print('Login success!')
        return connection
    else:
        print('Login failed')
        return None


async def retrieve_vehicles(connection):
    '''

    :param connection:
    :return:
    '''
    instruments = set()

    try:
        await connection.get_vehicles()
    except Exception as e:
        print(f'Error encountered when fetching vehicles: {e}')
        exit()

    # Need to get data before we know what sensors are available
    print('Fetch latest data for all vehicles.')
    try:
        await connection.update_all()
    except Exception as e:
        print(f'Error encountered when fetching vehicle data: {e}')
        exit()

    print('Vehicles successfully retrieved')

    for vehicle in connection.vehicles:

        print('Setting up dashboard')
        try:
            dashboard = vehicle.dashboard(mutable=True, miles=False)
            for instrument in (
                    instrument
                    for instrument in dashboard.instruments
                    if instrument.component in COMPONENTS and is_enabled(instrument.slug_attr)):
                instruments.add(instrument)
        except Exception as e:
            print(f'Failed to load instruments: {e}')
            exit()

    print('Dashboard setup finished successfully')


def get_vehicle_base_info(vehicle) -> dict:
    '''

    :param vehicle:
    :return:
    '''
    base_info = {
        'model': vehicle.model,
        'vin': vehicle.vin,
        'manufactured': vehicle.model_year,
        'connect_service_deactivated': vehicle.deactivated,
        'nickname': vehicle.nickname if vehicle.is_nickname_supported else None,
        'engine_capacity': vehicle.engine_capacity,
        'engine_type': vehicle.engine_type
    }
    return base_info
