import unidecode
import re
from typing import TypedDict
from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_file_handler, intent_handler
from libtado import api as tado_api


class TadoZoneDict(TypedDict):
    id: str
    name: int
    curr_temp: float


class TadoSkill(MycroftSkill):
    tado = None
    tado_zones_data: list[TadoZoneDict] = None
    username = None
    password = None
    client_secret = None
    temperature_unit = None

    def __init__(self):
        MycroftSkill.__init__(self)
        self.error_code = 0
        self.load_setting_variables()
        self.get_tado_api()

    def initialize(self):
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()

    def on_settings_changed(self):
        self.load_setting_variables()
        self.get_tado_api()

    @intent_file_handler('leaving_home.intent')
    def handle_tado_leaving(self, message):
        success = self.set_tado_state(False)
        if success:
            self.speak_dialog('error_unknown', data={'action': 'stopping'})
        else:
            self.speak_dialog('success', data={'action': 'stopped the heating '})

    @intent_file_handler('arriving_home.intent')
    def handle_tado_arriving(self, message):
        success = self.set_tado_state(True)
        if success:
            self.speak_dialog('error_unknown', data={'action': 'resuming'})
        else:
            self.speak_dialog('success', data={'action': 'resumed the heating'})

    @intent_handler(IntentBuilder('SetTemperatureIntent')
                    .require('Set')
                    .require('Room')
                    .require('To')
                    .require('Degrees')
                    )
    def handle_tado_set_temperature(self, message):
        utterance = message.data.get('utterance')
        self.log.info(f"=============> {utterance}")

        temp = re.findall("\d+", utterance)
        room = re.findall("(?<= )(.*)(?= room)", utterance)

        self.log.info(f"=============> {str(message.utterance_remainder())}")
        self.log.info(f"Temp read > {temp}")
        self.log.info(f"Zone read > {room}")
        temp = int(temp[0])
        room = str(room[0])

        if not room:
            self.speak_dialog('error_zone_missing', {'zone': room})
            room = self.get_response("request_zone")

        if not temp:
            self.speak_dialog('error_unknown', data={'action': 'setting'})

        self.read_zones_data_from_tado()
        zone_names = [zone_data["name"] for zone_data in self.tado_zones_data]
        if room and room in zone_names:
            self.set_tado_temperature(temp, room)
        else:
            self.speak_dialog('error_zone_missing', {'zone': room})
            room = self.get_response("request_zone")
            self.set_tado_temperature(temp, room)

    def load_setting_variables(self):
        self.username = self.settings.get('username')
        self.password = self.settings.get('password')
        self.client_secret = self.settings.get('client_secret')

    def get_tado_api(self):
        try:
            self.tado = tado_api.Tado(
                username=self.username,
                password=self.password,
                secret=self.client_secret,
            )
            self.set_user_temperature_unit()
        except:
            self.log.error(f"Authentication error. Please review the skill configuration.")

    def set_tado_state(self, state: bool) -> bool:
        try:
            self.tado.set_home_state(state)
            return True
        except:
            return False

    def set_tado_temperature(self, temp, room):
        success = False
        try:
            for zone in self.tado_zones_data:
                if zone["name"] == room:
                    self.tado.set_temperature(zone["id"], temp)
                    success = True
        except:
            pass

        if success:
            self.speak_dialog('success', data={'action': f"set the temperature to {temp} degrees"})
        else:
            self.speak_dialog('error_unknown', data={'action': 'setting'})

    def read_zones_data_from_tado(self):
        tado_zones_data: list[TadoZoneDict] = []
        try:
            for zone in self.tado.get_zones():
                zone_id = zone['id']
                state_data = self.tado.get_state(zone_id)
                user_temp_unit = self.get_user_temperature_unit()
                current_zone_temp = state_data['sensorDataPoints']['insideTemperature'][user_temp_unit]

                tado_zone_dict: TadoZoneDict = {
                    'id': zone_id,
                    'name': normalizeText(zone['name']),
                    'temp': current_zone_temp
                }
                tado_zones_data.append(tado_zone_dict)
            self.tado_zones_data = tado_zones_data
            self.log.info(f"Zones data > {tado_zones_data}")

        except:
            self.speak_dialog('error_unknown', data={'action': 'setting'})

    def get_user_temperature_unit(self) -> str:
        try:
            return self.tado.get_home()['temperatureUnit'].lower()
        except:
            return 'celsius'


def normalizeText(text: str) -> str:
    return unidecode.unidecode(text.lower())


def create_skill():
    return TadoSkill()

