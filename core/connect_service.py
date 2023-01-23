from aiohttp import ClientSession
from skodaconnect import Connection
from skodaconnect.vehicle import Vehicle

from core.config import COMPONENTS, is_enabled
from core.exceptions import AuthorizationError, VehicleRetrieveError, ServiceUpdateError, InstrumentLoadError


class ConnectService():
    '''Base connect service'''
    def __init__(self, name, email, password):
        self.__name = name
        self.__email = email
        self.__password = password # TODO: hash


class SkodaConnectService(ConnectService):
    '''Skoda Connect Service'''
    def __init__(self):
        super(ConnectService, self).__init__()

        self._print_response = False
        self._service_instance = None

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
                self.__email,
                self.__password,
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


class SkodaVehicle(Vehicle):
    def __init__(self):
        super(Vehicle, self).__init__()

    def get_vehicle_base_info(self) -> dict:
        '''

        :param vehicle:
        :return:
        '''
        base_info = {
            'model': self.model,
            'vin': self.vin,
            'manufactured': self.model_year,
            'connect_service_deactivated': self.deactivated,
            'nickname': self.nickname if self.is_nickname_supported else None,
            'engine_capacity': self.engine_capacity,
            'engine_type': self.engine_type
        }
        return base_info
