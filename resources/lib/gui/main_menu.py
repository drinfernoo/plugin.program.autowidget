class MainMenu():
    def __init__(self):
        pass
        
    def show_menu(self):
        from resources.lib.common import directory
        
        directory.add_menu_item(title='Add Path', params={'mode': 'path',
                                                          'action': 'add'},
                                description='Add a new path to be cycled.')
