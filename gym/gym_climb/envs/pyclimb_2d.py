import pygame
import pymunk
import pymunk.pygame_util
import os
import math
import sys
import random

screen_width = 1900
screen_height = 960
space = None

class Car:
    def __init__(self, space, maps, wheel_radius = 30):
        momentum = 1
        body_size = (200, 40)
        moment = pymunk.moment_for_box(momentum, body_size)
        self.body = pymunk.Body(momentum, moment)
        self.shape = pymunk.Poly.create_box(self.body, body_size)
        self.shape.mass = 5
        self.body.position = (200, 200)
        self.shape.body = self.body
        self.shape.color = (0, 0, 0, 255)

        human_moment = pymunk.moment_for_box(momentum, (30, 50))
        self.human_body = pymunk.Body(momentum, human_moment)
        self.human_shape = pymunk.Poly.create_box(self.human_body, (30, 50))
        self.human_body.position = (self.body.position.x, self.body.position.y+70)
        self.human_shape.body = self.human_body
        self.human_shape.color = (255, 0, 0, 255)
        self.human_joint = pymunk.PivotJoint(self.human_body, self.body, (-15, -20), (-15, 20))
        self.human_joint2 = pymunk.PivotJoint(self.human_body, self.body, (15, -20), (15, 20))

        head_moment = pymunk.moment_for_circle(momentum, 1, 1)
        self.head_body = pymunk.Body(momentum, head_moment)
        self.head_body.position = (self.human_body.position.x, self.human_body.position.y+70)
        self.head_shape = pymunk.Circle(self.head_body, 30)
        self.head_joint = pymunk.PivotJoint(self.head_body, self.human_body, (-10, -30), (-10, 20))
        self.head_joint2 = pymunk.PivotJoint(self.head_body, self.human_body, (10, -30), (10, 20))
        self.head_shape.collision_type = 1

        momentum = 100
        wheel_moment = pymunk.moment_for_circle(momentum, 10, wheel_radius)
        self.wheel1_body = pymunk.Body(momentum, wheel_moment)
        self.wheel1_body.position = self.body.position + (-60, -20)
        self.wheel1_shape = pymunk.Circle(self.wheel1_body, wheel_radius)
        self.wheel2_body = pymunk.Body(momentum, wheel_moment)
        self.wheel2_body.position = self.body.position + (60, -20)
        self.wheel2_shape = pymunk.Circle(self.wheel2_body, wheel_radius)

        self.wheel1_joint = pymunk.PivotJoint(self.body, self.wheel1_body, (-60, -20), (0, 0))
        self.wheel1_motor = pymunk.SimpleMotor(self.wheel1_body, self.body, 0)
        self.wheel2_joint = pymunk.PivotJoint(self.body, self.wheel2_body, (60, -20), (0, 0))

        self.wheel1_shape.friction = 1
        self.wheel1_shape.color = (200, 200, 200)
        self.wheel2_shape.friction = 1
        self.wheel2_shape.color = (200, 200, 200)

        space.add(self.body, self.shape)
        space.add(self.human_body, self.human_shape, self.human_joint, self.human_joint2)
        space.add(self.head_body, self.head_shape, self.head_joint, self.head_joint2)
        space.add(self.wheel1_body, self.wheel1_shape, self.wheel1_joint, self.wheel1_motor)
        space.add(self.wheel2_body, self.wheel2_shape, self.wheel2_joint)

        shape_filter = pymunk.ShapeFilter(group=1)
        self.shape.filter = shape_filter
        self.human_shape.filter = shape_filter
        self.head_shape.filter = shape_filter
        self.wheel1_shape.filter = shape_filter
        self.wheel1_motor.filter = shape_filter
        self.wheel2_shape.filter = shape_filter

        self.is_dead = False
        self.tick = 0
        self.prev_dist = 9999
        self.speed = 0
        self.face = pygame.image.load("normal.png")
        self.face = pygame.transform.scale(self.face, (90, 90))

        self.check = 0
        self.prev_check = 0
        self.timer = 0
        self.total_reward = 0

        self.maps = maps

        self.c_handler = space.add_collision_handler(1, 2)
        self.c_handler.begin = self.collision_handler

    def collision_handler(self, space, arbiter, data):
        self.is_dead = True
        return True

    def draw_image(self, screen):
        rotated_face = rot_center(self.face, math.degrees(self.head_body.angle))
        screen.blit(rotated_face, (self.head_body.position[0] - 35, screen_height - self.head_body.position[1] - 40))

    def get_shapes(self):
        return self.body, self.shape, \
        self.human_body, self.human_shape, self.human_joint, self.human_joint2, \
        self.head_body, self.head_shape, self.head_joint, self.head_joint2, \
        self.wheel1_body, self.wheel1_shape, self.wheel1_joint, self.wheel1_motor, \
        self.wheel2_body, self.wheel2_shape, self.wheel2_joint

    def set_position(self, x):
        self.body._set_position((self.body.position.x - x, int(self.body.position.y)))
        self.human_body._set_position((self.human_body.position.x - x, int(self.human_body.position.y)))
        self.head_body._set_position((self.head_body.position.x - x, int(self.head_body.position.y)))
        self.wheel1_body._set_position((self.wheel1_body.position.x - x, int(self.wheel1_body.position.y)))
        self.wheel2_body._set_position((self.wheel2_body.position.x - x, int(self.wheel2_body.position.y)))

    def update(self):
        if self.speed > 0:
            self.speed -= 0.5
        elif self.speed < 0:
            self.speed += 0.5

        if self.speed > 50:
            self.speed = 50
        elif self.speed < -20:
            self.speed = -20

        self.wheel1_motor.rate = -self.speed


        if self.check - self.prev_check == 0 and self.check != 50:
            self.tick += 1
        else:
            self.prev_check = self.check
            self.tick = 0

        if self.tick >= 300 or self.body.position.x < 0 and self.check < 50:
            self.is_dead = True


    def get_data(self):
        data = []

        data.append(int(math.degrees(self.body.angle)) % 360)
        data.append(int(self.speed / 10))
        #data.append(int(self.body.position.y / 100))
        #data.append(int(self.maps[self.check] / 100))
        #data.append(int(self.maps[self.check+1] / 100))

        return data

def add_land(space):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (0, 0)
    land = pymunk.Segment(body, (-100, -10), (99999, -10), 10)
    land.friction = 1
    land.collision_type = 2
    space.add(body, land)

def add_mountatins(space):
    x = 1000
    mountains = []
    mountains_shape = []
    maps = []
    for i in range(50):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (x, random.randint(-50, 0))
        vertices = []
        random_x = random.randint(5, 10)
        random_y = random_x * 50
        maps.append(random_y)
        for d in range(181):
            y = math.sin(math.radians(d)) * random_y
            vertices.append((d * random_x, y))

        x += 90 * random_x
        shape = pymunk.Poly(body, vertices)
        shape.friction = 1
        shape.collision_type = 2
        #space.add(body, shape)
        mountains.append([body, shape, False])
    return mountains, maps

def rot_center(image, angle):
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

class PyClimb2D:
    def __init__(self, is_render = True):
        if is_render:
            pygame.init()
            self.screen = pygame.display.set_mode((screen_width, screen_height))
            self.font = pygame.font.SysFont("Arial", 30)
            self.clock = pygame.time.Clock()
            self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
            self.goal = pygame.image.load("goal.jpg")

        self.game_speed = 60
        self.is_render = is_render

        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)

        add_land(self.space)
        self.mountains, self.maps = add_mountatins(self.space)
        self.car = Car(self.space, self.maps)

        self.distances = []
        for i, m in enumerate(self.mountains):
            self.distances.append([m[0].position.x, i])
        self.distances.append([self.distances[-1][0] + 2000, 50])
        self.distances.append([self.distances[-1][0] + 500, 51])


    def action(self, action):
        if action == 0:
            self.car.speed += 2
        elif action == 1:
            self.car.speed -= 2

        self.car.update()
        self.space.step(1/50.0)
        if self.car.body.position.x > screen_width/2:
            d = self.car.body.position.x - screen_width/2
            self.car.set_position(d)
            for i, m in enumerate(self.mountains):
                m[0]._set_position((m[0].position.x - d, m[0].position.y))

            for dis in self.distances:
                dis[0] -= d

        for i, m in enumerate(self.mountains):
            if m[0].position.x < screen_width + 100 and m[2] == False:
                m[2] = True
                self.space.add(m[0], m[1])

            if m[0].position.x < -2000:
                self.space.remove(m[0], m[1])
                self.mountains.remove(m)



    def evaluate(self):
        reward = 0

        angle = (math.degrees(self.car.body.angle) + 360) % 360
        if angle > 70 and angle < 270:
            reward -= 0.2
        #elif angle < 70:
            #reward += 0.1

        if self.distances[self.car.check][0] - self.car.body.position.x < self.car.prev_dist:
            reward += 0.1
            if self.car.speed >= 30:
                reward += 0.1
            if self.car.speed >= 40:
                reward += 0.3
            if self.car.speed >= 50:
                reward += 0.5

            if self.car.body.position.x > self.distances[self.car.check][0]:
                self.car.check += 1
            self.car.prev_dist = self.distances[self.car.check][0] - self.car.body.position.x
        else:
            reward = -0.1

        if self.car.is_dead:
            reward = -1000

        self.car.total_reward += reward
        return reward

    def is_done(self):
        if self.car.check >= 51 or self.car.is_dead or self.car.total_reward < -1000:
            return True
        return False

    def observe(self):
        # return state
        ret = self.car.get_data()
        return ret

    def view(self):
        # draw game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass

        self.screen.fill((255, 255, 255))
        self.space.debug_draw(self.draw_options)
        self.car.draw_image(self.screen)
        text = self.font.render("speed : " + str(int(self.car.speed)), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/3, 100)
        self.screen.blit(text, text_rect)

        text = self.font.render("reward : " + str(int(self.car.total_reward)), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/3, 150)
        self.screen.blit(text, text_rect)

        self.goal_position = self.distances[50][0]
        if self.distances[50][0] - 300 < screen_width:
            self.screen.blit(self.goal, (self.distances[50][0] - 300, screen_height - 500))

        for d in self.distances:
            if d[0] > 0 and d[0] < screen_width:
                text = self.font.render(str(d[1]), True, (0, 0, 0))
                text_rect = text.get_rect()
                text_rect.center = (d[0], 300)
                self.screen.blit(text, text_rect)

        pygame.display.flip()
        self.clock.tick(self.game_speed)

def rot_center(image, angle):
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image
