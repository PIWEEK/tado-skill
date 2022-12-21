from mycroft import MycroftSkill, intent_file_handler


class Tado(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('tado.intent')
    def handle_tado(self, message):
        self.speak_dialog('tado')


def create_skill():
    return Tado()

