from aiohttp import ClientSession
from skodaconnect import Connection
from skodaconnect.vehicle import Vehicle

from core.config import COMPONENTS, is_enabled
from core.exceptions import AuthorizationError, VehicleRetrieveError, ServiceUpdateError, InstrumentLoadError


class ConnectService():
    '''Base connect service'''
    def __init__(self, email, password):
        self._email = email
        self._password = password


class SkodaConnectService(ConnectService):
    '''Skoda Connect Service'''
    def __init__(self, email, password):
        super(SkodaConnectService, self).__init__(email, password)

        self._print_response = False
        self._service_instance = None

    @property
    def vehicles(self):
        return self._service_instance.vehicles

    def get_connection_instance(self):
        return self._service_instance

    async def session_init(self):
        '''

        :return:
        '''
        if self._service_instance:
            return

        session = ClientSession(headers={'Connection': 'keep-alive'})
        try:
            connection = Connection(
                session,
                self._email,
                self._password,
                self._print_response
            )
            login_success = await connection.doLogin()
        except Exception as e:
            raise AuthorizationError(f'Login failed {e}')

        if not login_success:
            raise AuthorizationError('Login failed. Please, verify if email or password is correct and try again.')

        self._service_instance = connection

    async def retrieve_vehicles(self):
        instruments = set()
        try:
            await self._service_instance.get_vehicles()
        except Exception as e:
            raise VehicleRetrieveError(f'Error encountered when fetching vehicles: {e}')

        try:
            await self._service_instance.update_all()
        except Exception as e:
            raise ServiceUpdateError(f'Error encountered when fetching vehicle data: {e}')

        for vehicle in self._service_instance.vehicles:
            try:
                dashboard = vehicle.dashboard(mutable=True, miles=False)
                for instrument in (
                        instrument
                        for instrument in dashboard.instruments
                        if instrument.component in COMPONENTS and is_enabled(instrument.slug_attr)):
                    instruments.add(instrument)
            except Exception as e:
                raise InstrumentLoadError(f'Failed to load instruments: {e}')


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
