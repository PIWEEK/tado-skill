from mycroft import MycroftSkill, intent_file_handler
from libtado import api as tado_api


class Tado(MycroftSkill):
    tado = None
    username = None
    password = None
    client_secret = None

    def __init__(self):
        MycroftSkill.__init__(self)
        self.load_setting_variables()
        self.get_tado_api()

    def initialize(self):
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()

    def on_settings_changed(self):
        self.load_setting_variables()
        self.get_tado_api()

    @intent_file_handler('tado.intent')
    def handle_tado(self, message):
        self.speak_dialog('tado')

        zones = self.tado.get_zones()
        self.log.info(f"Tado zones  > {zones}")

        # self.tado.set_temperature(0, 10)
        try:
            self.tado.set_home_state(False)
        except:
            pass

    def load_setting_variables(self):
        self.username = self.settings.get('username')
        self.password = self.settings.get('password')
        self.client_secret = self.settings.get('client_secret')

        self.log.info(f"Tado username  > {self.username}")
        self.log.info(f"Tado password  > {self.password}")
        self.log.info(f"Tado client_secret  > {self.client_secret}")

    def get_tado_api(self):
        try:
            self.tado = tado_api.Tado(
                username=self.username,
                password=self.password,
                secret=self.client_secret,
            )
        except:
            self.log.error(f"Authentication error. Please review the skill configuration.")


def create_skill():
    return Tado()

