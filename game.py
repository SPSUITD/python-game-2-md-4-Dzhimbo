import arcade

SCREEN_TITLE = "World of Chaos"
SCREEN_WIDTH = 1024  
SCREEN_HEIGHT = 768
AUDIO_DIRECTORY = "audio/"
IMAGES_DIRECTORY = "images/"
MAPS_DIRECTORY = "maps/"

PLAYER_JUMP_POWER = 13
PLAYER_GRAVITY = 6

def main():
    game = Game(0)  
    arcade.run()


class Game(arcade.Window):

    def __init__(self, level):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)
        self.map = None
        self.camera = None
        self.player = None
        self.map_index = level
        self.setup(level)

    def setup(self, level):
        self.map = Map()
        self.camera = Camera()
        self.player = Player()
        self.map_index = level
        self.map.setup(self.map_index)
        self.player.setup(self.map)
        self.camera.setup(self.map_index, self.player)
    
    def restart(self, with_level):
        self.map = None
        self.camera = None
        self.player = None
        self.setup(with_level)

    def on_update(self, delta_time):
        self.player.update()
        self.camera.update()

    def on_draw(self):
        self.clear()
        self.camera.bg_camera.use()  
        self.camera.draw_bg()  
        self.camera.main_camera.use()  
        self.map.scene.draw()
        self.player.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W:
            self.player.jump()
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.key_pressed_right = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.key_pressed_left = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W:
            self.player.jumping = False
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.key_pressed_right = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.key_pressed_left = False


class Player:

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self.player_sprite = arcade.Sprite(arcade.load_texture(IMAGES_DIRECTORY + "player.png"), 1)
        self.sprite_list.append(self.player_sprite)
        self.map = None
        self.key_pressed_left = False
        self.key_pressed_right = False
        self.speed = 0
        self.jump_timer = 0
        self.jumping = False
        self.on_ground = False

    def setup(self, _map):
        self.map = _map
        self.map.spawn_player(self.player_sprite)
        self.player_sprite.center_y += self.player_sprite.height / 2
    
    def draw(self):
        self.sprite_list.draw()

    def update(self):
        if self.key_pressed_right:
            self.speed = 5
        elif self.key_pressed_left:
            self.speed = -5
        else:
            self.speed = 0

        self.player_sprite.center_x += self.speed

        if self.jumping:
            self.jump_timer -= 1
            self.player_sprite.center_y += PLAYER_JUMP_POWER
            if self.jump_timer <= 0:
                self.jumping = False
        if not self.on_ground:
            self.player_sprite.center_y -= PLAYER_GRAVITY
        self.collision()

    def jump(self):  
        if self.on_ground:
            self.jumping = True
            self.jump_timer = 30

    def collision(self):
        if self.map.scene["collision"].__len__() > 0:
            distances = []
            for block in self.map.scene["collision"]:
                distances.append((pow((block.center_x - self.player_sprite.center_x), 2) + pow(
                    (block.center_y - self.player_sprite.center_y), 2)) ** 0.5)
            block_index = distances.index(min(distances))
            block = self.map.scene["collision"][block_index]
            if (self.player_sprite.right > block.left and self.player_sprite.left < block.right) \
                    and (self.player_sprite.top > block.bottom and self.player_sprite.bottom < block.top):
                self.on_ground = True
                if self.player_sprite.bottom < block.top - 15:
                    self.player_sprite.center_x -= 10
                    self.player_sprite.center_y -= 10
            else:
                self.on_ground = False


class Map:
    def __init__(self):
        self.tile_map = None
        self.scene = None
        self.level = 0

    def setup(self, index):
        self.level = index
        map_file = MAPS_DIRECTORY + f"map{index}.json"
        self.tile_map = arcade.load_tilemap(map_file, 1)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

    def spawn_player(self, player_sprite):
        player_sprite.position = self.scene["spawn"][0].position
        self.scene["spawn"].pop(0)


class Camera:
    def __init__(self):
        self.bg_camera = None
        self.main_camera = None
        self.bg_list = None
        self.map_index = 0
        self.player = None

    def setup(self, map_index, player):
        self.player = player
        self.bg_camera = arcade.Camera()
        self.main_camera = arcade.Camera()
        self.bg_list = []
        self.bg_list.append(arcade.load_texture(IMAGES_DIRECTORY + f"levelbg{map_index}.png"))
        self.map_index = map_index

    def update(self):
        self.center_camera_to_position(self.player.player_sprite.position)

    def center_camera_to_position(self, position):
        screen_center_x = position[0] - SCREEN_WIDTH / 2
        screen_center_y = position[1] - SCREEN_HEIGHT / 2
        self.main_camera.move_to([screen_center_x, screen_center_y])

    def draw_bg(self):
        arcade.draw_texture_rectangle(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT, self.bg_list[0])

main()
