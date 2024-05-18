from random import randrange
import arcade

SCREEN_TITLE = "World of Chaos"
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


AUDIO_DIRECTORY = "audio/"
IMAGES_DIRECTORY = "images/"
MAPS_DIRECTORY = "maps/"


PLAYER_MAX_HEALTH = 200
PLAYER_JUMP_POWER = 13
PLAYER_GRAVITY = 6

BULLETS_SPEED = [10, 8, 5, 20, 6, 15]
BULLETS_DAMAGE = [-10, -5, -25, -5, -30, -50]
BULLETS_LIFETIME = [50, 50, 75, 100, 125, 150]


ENEMY_HEALTH = [20, 10, 30, 40, 50, 100]
ENEMY_SCALE = [1, 0.8, 0.8, 1.5, 1.2, 1]
ENEMY_RADIOUS = [300, 300, 500, 500, 800, 800]
ENEMY_RELOAD = [20, 100, 20, 20, 20, 20]

SPRITES_ANIMATIONS_DELAY = 5

def main():
    game = Game(0)
    arcade.run()



class Game(arcade.Window):

    def __init__(self, level):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)
        self.setup(level)

    def setup(self, level):
        self.map = Map()
        self.camera = Camera()
        self.audio = Audio()
        self.player = Player()
        self.map_index = level
        self.bullets = Bullets(self.player, self.map)
        self.map.setup(self.map_index, self.bullets, self.player)
        self.audio.setup()
        self.audio.play_music(self.map_index)
        self.player.setup(self.map, self.audio, self.bullets)
        self.camera.setup(self.player, self.map_index)
        self.restarting = False


    def restart(self, with_level):
        self.audio.stop_music()
        self.map = None
        self.camera = None
        self.audio = None
        self.player = None
        self.restarting = True
        self.setup(with_level)



    def on_update(self, delta_time):

        if self.player.game_started and not self.player.game_win and not self.player.game_lose:
            self.player.update()
            self.camera.update(self.player.player_sprite.position[0] - SCREEN_WIDTH / 2)
            self.map.update(self.player.player_sprite.position)
            self.bullets.update()


    def on_draw(self):
        self.clear()
        self.camera.bg_camera.use()
        self.camera.draw_bg()
        self.camera.main_camera.use()
        self.map.scene.draw()
        self.map.draw()
        self.bullets.draw()
        self.player.draw()
        self.camera.gui_camera.use()
        self.camera.draw_gui()


    def on_key_press(self, key, modifiers):
        if self.map_index > 0 and not self.player.game_started:
            self.player.game_started = True
        elif not self.restarting and not self.player.game_lose and not self.player.game_win:
            if key == arcade.key.UP or key == arcade.key.W:
                self.player.jump()
            if key == arcade.key.SPACE:
                self.player.shoot()
            if key == arcade.key.RIGHT or key == arcade.key.D:
                self.player.key_pressed_right = True
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.player.key_pressed_left = True


    def on_key_release(self, key, modifiers):
        if not self.restarting and not self.player.game_lose and not self.player.game_win:
            if key == arcade.key.UP or key == arcade.key.W:
                self.player.jumping = False
            if key == arcade.key.RIGHT or key == arcade.key.D:
                self.player.key_pressed_right = False
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.player.key_pressed_left = False


    def on_mouse_press(self, x, y, button, modifiers):
        if not self.player.game_started and self.map_index == 0:
            if self.text_has_collision(x, y, self.camera.start_game):
                self.player.game_started = True
            elif self.text_has_collision(x, y, self.camera.exit_game):
                super().close()
        elif self.player.game_lose:
            if self.text_has_collision(x, y, self.camera.restart):
                self.restart(0)
            elif self.text_has_collision(x, y, self.camera.exit_game):
                super().close()
        elif self.player.game_win:
            if self.map_index >= 2:
                super().close()
            else:
                self.restart(self.map_index + 1)
    def text_has_collision(self, x, y, text):
        return (text.position[0] < x < (text.position[0] + text.content_width)
                and text.position[1] < y < (text.position[1] + text.content_height))


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

        self.map = None
        self.audio = None

        self.direction = False
        self.key_pressed_left = False
        self.key_pressed_right = False

        self.speed = 0
        self.jump_timer = 0
        self.jumping = False
        self.on_ground = False
        self.invulnerability_timer = 0
        self.big_bullets_timer = 0

        self.health = PLAYER_MAX_HEALTH

        self.game_started = False
        self.game_win = False
        self.game_lose = False

        self.sprite_change = 0

    def setup(self, _map, _audio, _bullets):
        self.map = _map
        self.audio = _audio
        self.bullets = _bullets


        self.map.spawn_player(self.player_sprite)
        self.player_sprite.center_y += self.player_sprite.height / 2


    def draw(self):
        self.sprite_list.draw()

    def update(self):

        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1
        elif self.invulnerability_timer == 0:
            self.player_sprite.alpha = 255
            self.invulnerability_timer -= 1

        if self.big_bullets_timer > 0:
            self.big_bullets_timer -= 1


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

        if self.player_sprite.top < 0:
            self.add_health(-PLAYER_MAX_HEALTH)
        collisions = ["collision", "damage", "invulnerability", "health"]
        for i in range(0, 4):
            if self.map.scene[collisions[i]].__len__() > 0:
                distances = []
                for block in self.map.scene[collisions[i]]:
                    distances.append((pow((block.center_x - self.player_sprite.center_x), 2) + pow(
                        (block.center_y - self.player_sprite.center_y), 2)) ** 0.5)
                block_index = distances.index(min(distances))
                block = self.map.scene[collisions[i]][block_index]

                if collisions[i] == 'collision':  
                    if (self.player_sprite.right > block.left and self.player_sprite.left < block.right) \
                            and (self.player_sprite.top > block.bottom and self.player_sprite.bottom < block.top):
                        self.on_ground = True  
                        if self.player_sprite.bottom < block.top - 15:
                            self.player_sprite.center_x -= 10  
                            self.player_sprite.center_y -= 10
                    else:  
                        self.on_ground = False 
                elif collisions[i] == 'damage':
                    if (self.player_sprite.right > block.left and self.player_sprite.left < block.right) \
                            and (self.player_sprite.top > block.bottom and self.player_sprite.bottom < block.top): 
                        self.map.scene['damage'][block_index].remove_from_sprite_lists()  
                        self.big_bullets_timer = 400
                elif collisions[i] == 'invulnerability':
                    if (self.player_sprite.right > block.left and self.player_sprite.left < block.right) \
                            and (self.player_sprite.top > block.bottom and self.player_sprite.bottom < block.top): 
                        self.map.scene['invulnerability'][block_index].remove_from_sprite_lists() 
                        self.invulnerability_timer = 300 
                        self.player_sprite.alpha = 100
                elif collisions[i] == 'health':
                    if (self.player_sprite.right > block.left and self.player_sprite.left < block.right) \
                            and (
                            self.player_sprite.top > block.bottom and self.player_sprite.bottom < block.top):
                        self.map.scene['health'][
                            block_index].remove_from_sprite_lists()  
                        self.add_health(50)  

        
        for i in range(0, self.map.enemys.__len__()):  
            if not self.map.enemys[i].dead:
                enemy_sprite = self.map.enemys[i].sprite  

                if (self.player_sprite.right > enemy_sprite.left and self.player_sprite.left < enemy_sprite.right) \
                        and (
                        self.player_sprite.top > enemy_sprite.bottom and self.player_sprite.bottom < enemy_sprite.top):
                    if self.player_sprite.bottom + 10 >= enemy_sprite.top and self.invulnerability_timer <= 0:
                        self.map.enemys[i].kill_enemy()
                    else:
                        self.damage_player(-10)
    def add_health(self, health):
        self.health = min(self.health + health, PLAYER_MAX_HEALTH)
        if self.health <= 0:
            self.game_lose = True
            self.health = 0

    def damage_player(self, damage):
        if self.invulnerability_timer <= 0:
            self.invulnerability_timer = 60
            self.player_sprite.alpha = 100
            self.add_health(damage)

    
    def shoot(self):
        isRight = 1
        if not self.direction:
            isRight *= -1
        direction = [self.player_sprite.center_x - self.player_sprite.center_x + isRight, 0]
        sprite_index = 0
        if randrange(0, 2) == 1:
            sprite_index = 1

        scale = 1
        if self.big_bullets_timer > 0:
            scale = 3
        self.bullets.spawn_bullet(self.player_sprite.position, direction,
                                  IMAGES_DIRECTORY + "player_attack_" + str(sprite_index) + ".png", 0, True, scale)
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



class Map:
    def __init__(self):
        self.tile_map = None
        self.scene = None
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
        self.enemySpriteList.draw()
        for enemy in self.enemys:
            enemy.draw()

    def update(self, player_pos):  
        for enemy in self.enemys:
            enemy.update(player_pos)

    def check_for_level_complete(self):
        all_enemy_dead = True
        for enemy in self.enemys:
            if not enemy.dead:
                all_enemy_dead = False
        if all_enemy_dead:
            self.player.game_win = True




    class Enemy:  
        def __init__(self, sprite, _type, _map, _bullets):
            self.direction = True
            self.speed = 2
            self.dead = False
            #  Тип врага
            self.enemyType = _type
            self.reload = 0
            self.health = ENEMY_HEALTH[_type]
            self.tex_right = arcade.load_texture(IMAGES_DIRECTORY + "enemy" + str(int(self.enemyType)) + ".png")
            self.tex_left = self.tex_right.flip_horizontally()

            self.sprite = arcade.Sprite(self.tex_right, ENEMY_SCALE[_type])
            self.sprite.position = sprite.position 
            self.sprite.center_y -= 3 
            self.map = _map
            self.bullets = _bullets

        def update(self, player_pos):
            if not self.dead:  
                distance = (pow((self.sprite.position[0] - player_pos[0]), 2) + pow(
                    (self.sprite.position[1] - player_pos[1]), 2)) ** 0.5
                if distance < ENEMY_RADIOUS[self.enemyType] and abs(self.sprite.center_y - player_pos[1]) < 100:
                    self.shoot(player_pos)
                else:
                    if self.direction:
                        self.sprite.center_x += self.speed
                    else:
                        self.sprite.center_x -= self.speed
                    self.collision()

        def draw(self):
            if not self.dead:
                health_offset = [self.sprite.center_x - 64, self.sprite.center_y + 64]
                size = [128, 15]
                arcade.draw_xywh_rectangle_filled(health_offset[0], health_offset[1], size[0], size[1],
                                                  arcade.csscolor.BLACK)
                arcade.draw_xywh_rectangle_filled(health_offset[0] + 4, health_offset[1] + 4,
                                                  (size[0] - 8) * self.health / ENEMY_HEALTH[self.enemyType],
                                                  size[1] - 8, arcade.csscolor.RED)

        def shoot(self, player_pos):  
            if self.reload == 0:
                if ((self.sprite.position[0] > player_pos[0] and self.direction) or
                        (self.sprite.position[0] < player_pos[0] and not self.direction)):
                    self.switch_direction()
                direction = [1, 0]
                if player_pos[0] < self.sprite.position[0]:
                    direction = [-1, 0]
                self.reload = ENEMY_RELOAD[self.enemyType]
                self.bullets.spawn_bullet(self.sprite.position, direction, IMAGES_DIRECTORY + "enemy" +
                                          str(self.enemyType) + "_attack.png", self.enemyType, False, 1)
            else:
                self.reload -= 1

        def collision(self):

            distances = []
            for block in self.map.scene["collision"]:
                distances.append((pow((block.center_x - self.sprite.center_x), 2) + pow(
                    (block.center_y - self.sprite.center_y), 2)) ** 0.5)
            block_index = distances.index(min(distances))  
            block = self.map.scene["collision"][block_index]



            if not ((block.left <= self.sprite.center_x <= block.right) and (self.sprite.bottom <= block.top)):
                self.switch_direction()

        def switch_direction(self):

            if self.direction:
                self.direction = False
                self.sprite.texture = self.tex_left
            else:
                self.direction = True
                self.sprite.texture = self.tex_right

        def damage_enemy(self, damage):
            self.health += damage
            if self.health <= 0:
                self.kill_enemy()

        def kill_enemy(self):
            self.dead = True
            self.sprite.center_x = -500
            self.sprite.scale = 0
            self.map.check_for_level_complete()


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
            for i in range(0, length):
                self.bullets[i].update(self.player, self.map.enemys)
                if self.bullets[i].lifetime <= 0:
                    self.bullet_list.pop(i)
                    self.bullets.pop(i)
                    break  

    def spawn_bullet(self, position, direction, sprite, _type, friendly_bullet, scale):
        new_bullet = Bullet(position, direction, sprite, BULLETS_SPEED[_type], BULLETS_DAMAGE[_type],
                            BULLETS_LIFETIME[_type], friendly_bullet, scale)
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
        else:  
            player_pos = player.player_sprite.position
            distance = (pow((self.bullet_sprite.position[0] - player_pos[0]), 2) + pow(
                (self.bullet_sprite.position[1] - player_pos[1]), 2)) ** 0.5
            if distance < 30:
                player.damage_player(self.damage)
                self.lifetime = 0



class Camera:
    def __init__(self):
        self.position_x = 0
        self.bg_camera = None
        self.main_camera = None
        self.gui_camera = None
        self.player = None
        self.bg_list = None
        self.player_health = arcade.SpriteList()
        self.player_health.append(arcade.Sprite(IMAGES_DIRECTORY + "player_health.png", 2, 90, 50))
        self.welcome_screen = arcade.SpriteList()
        self.welcome_screen.append(
            arcade.Sprite(IMAGES_DIRECTORY + "start_screen.png", 1, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.win_screen = arcade.SpriteList()
        self.win_screen.append(
            arcade.Sprite(IMAGES_DIRECTORY + "win_screen.png", 1, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.next_level_screen = arcade.SpriteList()
        self.next_level_screen.append(
            arcade.Sprite(IMAGES_DIRECTORY + "next_level_screen.png", 1, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.lose_screen = arcade.SpriteList()
        self.lose_screen.append(
            arcade.Sprite(IMAGES_DIRECTORY + "lose_screen.png", 1, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.start_game = arcade.Text("Начать игру", int(SCREEN_WIDTH / 2 - 180), int(SCREEN_HEIGHT / 2 - 250),
                                      arcade.color.AQUA, 64, None, "center",
                                      "impact", True)
        self.restart = arcade.Text("Рестарт", int(SCREEN_WIDTH / 2 - 130), int(SCREEN_HEIGHT / 2 - 250),
                                   arcade.color.YELLOW, 64, None, "center",
                                   "impact", True)
        self.exit_game = arcade.Text("Выход", int(SCREEN_WIDTH / 2 - 100), int(SCREEN_HEIGHT / 2 - 350),
                                     arcade.color.RED,
                                     64, None, "center", "impact", True)
    def setup(self, player, map_index):

        self.bg_camera = arcade.Camera()
        self.main_camera = arcade.Camera()
        self.gui_camera = arcade.Camera()

        self.bg_list = []
        self.bg_list.append(
            arcade.load_texture(IMAGES_DIRECTORY + f"levelbg{map_index}.png"))  
        self.map_index = map_index
        self.player = player

    def update(self, left_border):
        self.center_camera_to_position(self.player.player_sprite.position)
    def center_camera_to_position(self, position):
        screen_center_x = self.lerp(self.main_camera.position[0], position[0] - (SCREEN_WIDTH / 2), 0.1)
        screen_center_y = self.lerp(self.main_camera.position[1], position[1] - (SCREEN_HEIGHT / 2), 0.1)
        self.main_camera.move_to([screen_center_x, screen_center_y])

    def move_camera(self, speed, player_pos):
        position = self.position_x, 0
        self.main_camera.move_to(position)
    def draw_bg(self):
       
        arcade.draw_texture_rectangle(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT, self.bg_list[0])
    def draw_gui(self):

      
        health_offset = [55, 30]
        size = [100, 20]
        self.player_health.draw()

        arcade.draw_xywh_rectangle_filled(health_offset[0] + 4,
                                          health_offset[1] + 4, (size[0] - 8) * self.player.health / PLAYER_MAX_HEALTH,
                                          size[1] - 8, arcade.csscolor.GREEN)

        if not self.player.game_started:
            if self.map_index > 0:
                self.next_level_screen.draw()
            else:
                self.welcome_screen.draw()
                self.start_game.draw()
                self.exit_game.draw()

        elif self.player.game_lose:
            self.lose_screen.draw()
            self.restart.draw()
            self.exit_game.draw()
        elif self.player.game_win:
            self.win_screen.draw()
    def lerp(self, a, b, t):
        return (1 - t) * a + t * b


class Audio:

    def __init__(self):
        self.music = None
        self.sounds = None
        self.media_player = None
        self.isPlaying = False

    def setup(self):
        self.music = [arcade.load_sound(AUDIO_DIRECTORY + "game_level_0.mp3"),
                      arcade.load_sound(AUDIO_DIRECTORY + "game_level_1.mp3"),
                      arcade.load_sound(AUDIO_DIRECTORY + "game_level_2.mp3")]

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
