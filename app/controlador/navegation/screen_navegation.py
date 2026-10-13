# /MoringaCIP/app/controlador/navegation/screen_navegation.py
class ScreenNavegation:
    """Navega sobre el QStackedWidget existente creado por Qt Designer."""

    def __init__(self, stacked_widget):
        self.stacked_widget = stacked_widget
        # Guardar las páginas permite conservar su identidad si se reordenan.
        self.principal = stacked_widget.widget(0)
        self.vision_artificial = stacked_widget.widget(1)
        self.configurar_camara = stacked_widget.widget(2)
        self.configurar_plc = stacked_widget.widget(3)

    def screen_principal(self):
        self.stacked_widget.setCurrentWidget(self.principal)

    def screen_vision_artificial(self):
        self.stacked_widget.setCurrentWidget(self.vision_artificial)

    def screen_configurar_camara(self):
        self.stacked_widget.setCurrentWidget(self.configurar_camara)

    def screen_configurar_plc(self):
        self.stacked_widget.setCurrentWidget(self.configurar_plc)

     
