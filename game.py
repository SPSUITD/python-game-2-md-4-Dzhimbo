from random import randrange
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
        self.bullets = None
        self.audio = Audio()
        self.map_index = level
        self.setup(level)

    def setup(self, level):
        self.map = Map()
        self.camera = Camera()
        self.player = Player()
        self.audio = Audio()
        self.bullets = Bullets(self.player, self.map)
        self.map_index = level
        self.audio.play_music(level)
        self.map.setup(self.map_index, self.bullets, self.player)
        self.player.setup(self.map, self.bullets)
        self.camera.setup(self.map_index, self.player)
    
    def restart(self, with_level):
        self.map = None
        self.camera = None
        self.player = None
        self.setup(with_level)

    def on_update(self, delta_time):
        self.player.update()
        if not self.player.game_lose:
            self.map.update(self.player.player_sprite.position)
        else:
            self.map.update([0, 0])
        self.camera.update()
        self.bullets.update()

    def on_draw(self):
        self.clear()
        self.camera.bg_camera.use()  
        self.camera.draw_bg()  
        self.camera.main_camera.use()
        self.map.draw()
        self.bullets.draw()
        self.player.draw()

    def on_key_press(self, key, modifiers):
        if not self.player.game_lose:
            if key == arcade.key.SPACE:
                self.player.shoot()
            if key == arcade.key.UP or key == arcade.key.W:
                self.player.jump()
            if key == arcade.key.RIGHT or key == arcade.key.D:
                self.player.key_pressed_right = True
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.player.key_pressed_left = True

    def on_key_release(self, key, modifiers):
        if not self.player.game_lose:
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
        self.bullets = None
        self.key_pressed_left = False
        self.key_pressed_right = False
        self.speed = 0
        self.jump_timer = 0
        self.jumping = False
        self.on_ground = False
        self.direction = False

        self.health = 100
        self.game_lose = False

    def setup(self, _map, _bullets):
        self.map = _map
        self.bullets = _bullets
        self.map.spawn_player(self.player_sprite)
        self.player_sprite.center_y += self.player_sprite.height / 2
    
    def draw(self):
        if not self.game_lose:
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

    def shoot(self):
        is_right = 1
        if not self.direction:
            is_right *= -1
        direction = [self.player_sprite.center_x - self.player_sprite.center_x + is_right, 0]
        sprite_index = 0
        if randrange(0, 2) == 1:
            sprite_index = 1
        self.bullets.spawn_bullet(self.player_sprite.position, direction,
                                  IMAGES_DIRECTORY + "player_attack_" + str(sprite_index) + ".png", 0, True, 1)

    def animate_player(self):
        if not self.on_ground:
            if self.direction:
                self.player_sprite.texture = self.tex_fly_right
            else:
                self.player_sprite.texture = self.tex_fly_left
        elif not self.key_pressed_right and not self.key_pressed_left:
            if self.direction:
                self.player_sprite.texture = self.tex_right
            else:
                self.player_sprite.texture = self.tex_left
        else:
            if self.sprite_change <= 0:
                self.sprite_change = SPRITES_ANIMATIONS_DELAY
                self.current_walk_sprite_id += 1
                if self.current_walk_sprite_id > 2:
                    self.current_walk_sprite_id = 0
                if self.direction:
                    self.player_sprite.texture = self.tex_walk_right[self.current_walk_sprite_id]
                else:
                    self.player_sprite.texture = self.tex_walk_left[self.current_walk_sprite_id]
            else:
                self.sprite_change -= 1

    def add_health(self, health):
        self.health = self.health + health
        if self.health <= 0:
            self.game_lose = True
            self.health = 0

class Bullets:

    def __init__(self, _player, _map):
        self.player = _player
        self.map = _map
        self.bullet_list = arcade.SpriteList()
        self.bullets = []

    def draw(self):
        if len(self.bullet_list) > 0:
            self.bullet_list.draw()

    def update(self):
        length = self.bullet_list.__len__()
        if length > 0:
            for i in range(0, length):  # Для каждой пули в цикле
                self.bullets[i].update(self.player, self.map.enemys)  # Обновляем
                if self.bullets[i].lifetime <= 0:  # Если жизнь пули меньше или = 0, то удаляем её
                    self.bullet_list.pop(i)
                    self.bullets.pop(i)
                    break  # Выход из цикла чтоб не было ошибок

    def spawn_bullet(self, position, direction, sprite, _type, friendly_bullet, scale):
        new_bullet = Bullet(position, direction, sprite, 10, 10,
                            100, friendly_bullet, scale)
        self.bullets.append(new_bullet)
        self.bullet_list.append(new_bullet.bullet_sprite)


class Bullet:
    def __init__(self, position, direction, path_to_sprite, speed, damage, lifetime, friendly_button, scale):
        tex = arcade.load_texture(path_to_sprite)
        if direction[0] < 0:
            tex = tex.flip_horizontally()
        self.bullet_sprite = arcade.Sprite(tex, scale)
        self.bullet_sprite.position = position
        self.bullet_direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.friendly_button = friendly_button

    def update(self, player, enemy_list):
        self.bullet_sprite.center_x += (self.bullet_direction[0] * self.speed)
        self.bullet_sprite.center_y += (self.bullet_direction[1] * self.speed)
        self.lifetime -= 1
        if self.friendly_button:
            distances = []
            if enemy_list.__len__() > 0:
                for enemy in enemy_list:
                    distances.append((pow((self.bullet_sprite.position[0] - enemy.sprite.position[0]), 2) + pow(
                        (self.bullet_sprite.position[1] - enemy.sprite.position[1]), 2)) ** 0.5)
                min_distance = min(distances)
                if min_distance < 30 * self.bullet_sprite.scale:
                    enemy_index = distances.index(min_distance)
                    enemy_list[enemy_index].damage_enemy(self.damage)
                    self.lifetime = 0
        else:  # Иначе это вражеская пуля
            player_pos = player.player_sprite.position
            distance = (pow((self.bullet_sprite.position[0] - player_pos[0]), 2) + pow(
                (self.bullet_sprite.position[1] - player_pos[1]), 2)) ** 0.5
            if distance < 30:  # Если дистанция пули между игроком меньше 30, то попали
                player.add_health(-self.damage)
                self.lifetime = 0


class Map:
    def __init__(self):
        self.tile_map = None
        self.scene = None
        self.player = None
        self.bullets = None
        self.enemys = []
        self.game = 0
        self.level = 0
        self.enemySpriteList = arcade.SpriteList()

    def setup(self, index, _bullets, player):
        self.level = index
        self.bullets = _bullets
        self.player = player
        map_file = MAPS_DIRECTORY + f"map{index}.json"
        self.tile_map = arcade.load_tilemap(map_file, 1)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        for i in range(0, 6):
            enemystr = "enemy" + str(i)
            if self.scene.__contains__(enemystr):
                while self.scene[enemystr].__len__() > 0:
                    enemy = self.Enemy(self.scene[enemystr][0], i, self, self.bullets)
                    self.enemys.append(enemy)
                    self.enemySpriteList.append(enemy.sprite)
                    self.scene[enemystr].pop(0)

    def spawn_player(self, player_sprite):
        player_sprite.position = self.scene["spawn"][0].position
        self.scene["spawn"].pop(0)

    def draw(self):
        self.scene.draw()
        self.enemySpriteList.draw()

    def update(self, player_pos):
        for enemy in self.enemys:
            enemy.update(player_pos)

    class Enemy:

        def __init__(self, sprite, _type, _map, _bullets):
            self.direction = True
            self.speed = 2
            self.dead = False
            self.enemyType = _type
            self.reload = 0
            self.health = 1
            self.tex_right = arcade.load_texture(IMAGES_DIRECTORY + "enemy" + str(int(self.enemyType)) + ".png")
            self.tex_left = self.tex_right.flip_horizontally()

            self.sprite = arcade.Sprite(self.tex_right, 1)
            self.sprite.position = sprite.position
            self.sprite.center_y -= 3
            self.map = _map
            self.bullets = _bullets

        def update(self, player_pos):
            if not self.dead:  # Если враг жив
                distance = (pow((self.sprite.position[0] - player_pos[0]), 2) + pow(
                    (self.sprite.position[1] - player_pos[1]), 2)) ** 0.5
                if distance < 300:
                    self.shoot(player_pos)
                else:
                    if self.direction:  # Если направление == TRUE, то идёт направо, иначе налево
                        self.sprite.center_x += self.speed
                    else:
                        self.sprite.center_x -= self.speed
                    self.collision()  # Столкновения

        def collision(self):
            distances = []
            for block in self.map.scene["collision"]:
                distances.append((pow((block.center_x - self.sprite.center_x), 2) + pow(
                    (block.center_y - self.sprite.center_y), 2)) ** 0.5)
            block_index = distances.index(min(distances))
            block = self.map.scene["collision"][block_index]
            if not ((block.left <= self.sprite.center_x <= block.right) and (self.sprite.bottom <= block.top)):
                self.switch_direction()

        def shoot(self, player_pos):  # Стрельба врага по игроку.
            if self.reload == 0:
                if ((self.sprite.position[0] > player_pos[0] and self.direction) or
                        (self.sprite.position[0] < player_pos[0] and not self.direction)):
                    self.switch_direction()
                direction = [1, 0]
                if player_pos[0] < self.sprite.position[0]:
                    direction = [-1, 0]
                self.reload = 20
                self.bullets.spawn_bullet(self.sprite.position, direction, IMAGES_DIRECTORY + "enemy" +
                                          str(self.enemyType) + "_attack.png", self.enemyType, False, 1)
            else:
                self.reload -= 1

        def switch_direction(self):
            if self.direction:
                self.direction = False
                self.sprite.texture = self.tex_left
            else:
                self.direction = True
                self.sprite.texture = self.tex_right

        def damage_enemy(self, damage):
            self.health -= damage
            if self.health <= 0:
                self.kill_enemy()

        def kill_enemy(self):
            self.dead = True
            self.sprite.center_x = -500
            self.sprite.scale = 0


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


class Audio:

    def __init__(self):
        self.media_player = None
        self.isPlaying = False
        self.music = [arcade.load_sound(AUDIO_DIRECTORY + "game_level_0.mp3"),
                      arcade.load_sound(AUDIO_DIRECTORY + "game_level_1.mp3"),
                      arcade.load_sound(AUDIO_DIRECTORY + "game_level_2.mp3")]
        
# Методы проигрывания музыки и остановки музыки
    def play_music(self, level):  
        if self.isPlaying:
            self.stop_music()
        self.media_player = self.music[level].play()
        self.isPlaying = True

    def stop_music(self):  
        if self.isPlaying:
            arcade.stop_sound(self.media_player)
        self.isPlaying = False


main()

