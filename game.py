import arcade

SCREEN_TITLE = "World of Chaos"
SCREEN_WIDTH = 1024  
SCREEN_HEIGHT = 768
AUDIO_DIRECTORY = "audio/"
IMAGES_DIRECTORY = "images/"
MAPS_DIRECTORY = "maps/"

PLAYER_JUMP_POWER = 13
PLAYER_GRAVITY = 6

SPRITES_ANIMATIONS_DELAY = 5

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
        self.audio = Audio()
        self.map_index = level
        self.setup(level)

    def setup(self, level):
        self.map = Map()
        self.camera = Camera()
        self.player = Player()
        self.audio = Audio()
        self.map_index = level
        self.audio.play_music(level)
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
        self.tex_right = arcade.load_texture(IMAGES_DIRECTORY + "player.png")
        self.tex_left = self.tex_right.flip_horizontally()
        self.player_sprite = arcade.Sprite(self.tex_right, 1)
        self.sprite_list.append(self.player_sprite)

        self.tex_fly_right = arcade.load_texture(IMAGES_DIRECTORY + "player_jump.png")
        self.tex_fly_left = self.tex_fly_right.flip_horizontally()
        self.current_walk_sprite_id = 0
        self.tex_walk_right = []
        self.tex_walk_left = []
        for i in range(0, 3):
            self.tex_walk_right.append(arcade.load_texture(IMAGES_DIRECTORY + "player_walk_" + str(i) + ".png"))
            self.tex_walk_left.append(self.tex_walk_right[i].flip_horizontally())

        self.sprite_change = 0
        self.map = None
        self.key_pressed_left = False
        self.key_pressed_right = False
        self.speed = 0
        self.jump_timer = 0
        self.jumping = False
        self.on_ground = False
        self.direction = False

    def setup(self, _map):
        self.map = _map
        self.map.spawn_player(self.player_sprite)
        self.player_sprite.center_y += self.player_sprite.height / 2
    
    def draw(self):
        self.sprite_list.draw()

    def update(self):
        if self.key_pressed_right:
            self.speed = 5
            self.direction = True
        elif self.key_pressed_left:
            self.speed = -5
            self.direction = False
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
        self.animate_player()

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

    def animate_player(self):
        if not self.on_ground:  # Чел летит
            if self.direction:
                self.player_sprite.texture = self.tex_fly_right
            else:
                self.player_sprite.texture = self.tex_fly_left
        elif not self.key_pressed_right and not self.key_pressed_left:  # Чел стоит
            if self.direction:
                self.player_sprite.texture = self.tex_right
            else:
                self.player_sprite.texture = self.tex_left
        else:  # Чел бегает
            if self.sprite_change <= 0:  # если таймер смены картинки достиг 0, значит пора менять картинку
                self.sprite_change = SPRITES_ANIMATIONS_DELAY
                self.current_walk_sprite_id += 1
                if self.current_walk_sprite_id > 2:  # текущая ID картинки
                    self.current_walk_sprite_id = 0  # если ID > количества картинок (в случае с бегом 3 картинки), то делаем её равной 0
                if self.direction:
                    self.player_sprite.texture = self.tex_walk_right[self.current_walk_sprite_id]
                else:
                    self.player_sprite.texture = self.tex_walk_left[self.current_walk_sprite_id]
            else:
                self.sprite_change -= 1  # понижаем наш таймер смены картинки



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
        screen_center_x = self.lerp(self.main_camera.position[0], position[0] - (SCREEN_WIDTH / 2), 0.1)
        screen_center_y = self.lerp(self.main_camera.position[1], position[1] - (SCREEN_HEIGHT / 2), 0.1)
        self.main_camera.move_to([screen_center_x, screen_center_y])

    def draw_bg(self):
        arcade.draw_texture_rectangle(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT, self.bg_list[0])

    def lerp(self, a, b, t):
        return (1 - t) * a + t * b


class Audio:

    def __init__(self):
        self.media_player = None
        self.isPlaying = False
        self.music = [arcade.load_sound(AUDIO_DIRECTORY + "game_level_0.mp3"),
                      arcade.load_sound(AUDIO_DIRECTORY + "game_level_1.mp3"),
                      arcade.load_sound(AUDIO_DIRECTORY + "game_level_2.mp3")]

    def play_music(self, level):  # Метод проигрывания музыки
        if self.isPlaying:
            self.stop_music()
        self.media_player = self.music[level].play()
        self.isPlaying = True

    def stop_music(self):  # Метод остановки музыки
        if self.isPlaying:
            arcade.stop_sound(self.media_player)
        self.isPlaying = False


main()


