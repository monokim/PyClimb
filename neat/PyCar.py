import pygame
import pymunk
import pymunk.pygame_util
import os
import math
import sys
import random
import neat

screen_width = 1900
screen_height = 960
space = None
generation = 0
best_fitness = 0
show_cnt = 0
show_flag = False

class Car:
    def __init__(self, wheel_radius = 30, speed = 0, wheel_type="round"):
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
        self.head_shape.collision_type = 0

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
        self.speed = speed
        self.face = pygame.image.load("normal.png")
        self.face = pygame.transform.scale(self.face, (90, 90))

        self.check = 0
        self.prev_check = 0
        self.timer = 0

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

    def set_colors(self, body_color = (240, 240, 240), human_color = (240, 240, 240), wheel_color = (240, 240, 240)):
        self.shape.color = body_color
        self.human_shape.color = human_color
        self.head_shape.color = human_color
        self.wheel1_shape.color = wheel_color
        self.wheel2_shape.color = wheel_color

    def update(self):
        if self.speed < 50:
            self.speed += 1

        if self.speed < -20:
            self.speed = -20

        self.wheel1_motor.rate = -self.speed

        if self.check - self.prev_check == 0 and self.check != 50:
            self.tick += 1
        else:
            self.prev_check = self.check
            self.tick = 0

        if self.tick >= 300:
            self.is_dead = True

    def get_data(self, screen):
        """
        radar = [-100, 0, 100, 300, 500]
        data = []
        for r in radar:
            x = self.body.position.x + r
            if x < 0:
                x = 0
            if x >= screen_width:
                x = screen_width - 1
            y = self.body.position.y
            for i in range(screen_height-1, 0, -1):
                if screen.get_at((int(x), int(i))) != (39, 174, 96, 255):
                    data.append(i / screen_height)
                    break
        """
        for i in range(screen_height - 1, 0, -1):
            x = int(self.head_body.position.x)
            if x < 0:
                x = 0
            if screen.get_at((x, int(i))) != (39, 174, 96, 255):
                #print(abs(i - (screen_height - self.head_body.position.y)))
                if abs(i - (screen_height - self.head_body.position.y)) <= 50:
                    self.is_dead = True
                break

        #data = []
        #data.append(self.speed / 50.0)
        #data.append(math.degrees(self.body.angle) % 360 / 360.0)
        #data.append(self.body.position.y / screen_height)
        #data.append(self.head_body.position.y / screen_height)
        #return data
        return [math.degrees(self.body.angle) % 360 / 360.0]

def add_land(space):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (0, 0)
    land = pymunk.Segment(body, (-100, -10), (99999, -10), 10)
    land.friction = 1
    space.add(land)

def add_mountatins(space):
    x = 1000
    mountains = []
    mountains_shape = []
    for i in range(50):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (x, random.randint(-50, 0))
        vertices = []
        random_x = random.randint(5, 10)
        random_y = random_x * 50
        for i in range(181):
            y = math.sin(math.radians(i)) * random_y
            vertices.append((i * random_x, y))

        x += 90 * random_x
        shape = pymunk.Poly(body, vertices)
        shape.friction = 1
        shape.collision_type = 0
        #space.add(body, shape)
        mountains.append([body, shape, False])
    return mountains

def rot_center(image, angle):
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image

def draw_network(screen, x_pad = 0, y_pad = 0):
    font = pygame.font.SysFont("Arial", 30)
    black = (0, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    red = (255, 0, 0)


    x = 200 + x_pad
    list = [["speed", (x, 50 + y_pad)],
            ["angle", (x, 90 + y_pad)],\
            ["distance", (x, 130 + y_pad)],\
            ["gradient", (x, 170 + y_pad)],\
            ["bias", (x, 210 + y_pad)]]
    for l in list:
        pygame.draw.circle(screen, (0, 0, 0), l[1], 15, 2)
        text = font.render(l[0], True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (l[1][0] - 100, l[1][1])
        screen.blit(text, text_rect)


    x = 500 + x_pad
    list = [["Accel", (500 + x_pad, 90 + y_pad)],\
            ["Break", (500 + x_pad, 150 + y_pad)]]
    list = ["Accel", "Break"]
    for i, y in enumerate(range(90 + x_pad, 160 + x_pad, 60)):
        pygame.draw.circle(screen, (0, 0, 0), (x, y), 15, 2)
        text = font.render(list[i], True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (x + 100, y)
        screen.blit(text, text_rect)

    #for i, y in enumerate(range(50+x_pad, 220+x_pad, 40)):
        #pygame.draw.line(screen, black, )

def run_test():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    generation_font = pygame.font.SysFont("Arial", 70)
    font = pygame.font.SysFont("Arial", 30)
    goal_position = 3800
    goal_image = pygame.image.load("goal.png")

    global space
    space = pymunk.Space()
    space.gravity = (0.0, -900.0)

    add_land(space)
    mountains = add_mountatins(space)


    car = Car()

    #main game
    global generation
    generation += 1
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    car.body.angle += math.radians(30)
                elif event.key == pygame.K_LEFT:
                    car.body.angle -= math.radians(30)

        keys=pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            car.speed += 2
        elif keys[pygame.K_DOWN]:
            car.speed -= 3

        #print(pygame.mouse.get_pos(), screen.get_at(pygame.mouse.get_pos()))

        # check
        car.update()
        car.get_data(screen)
        space.step(1/50.0)

        if car.body.position.x > screen_width/2:
            d = car.body.position.x - screen_width/2
            car.set_position(d)
            for i, m in enumerate(mountains):
                m[0]._set_position((m[0].position.x - d, m[0].position.y))

            if len(mountains) == 0:
                goal_position -= d

        for i, m in enumerate(mountains):
            if m[0].position.x < 3000 and m[2] == False:
                m[2] = True
                space.add(m[0], m[1])

            #if m[0].position.x < -2000:
                #space.remove(m[0], m[1])
                #mountains.remove(m)
        #drawing
        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)
        car.draw_image(screen)

        text = generation_font.render("Generation : " + str(generation), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/2, screen_height/2 - 100)
        screen.blit(text, text_rect)

        text = font.render("speed : " + str(int(car.speed)), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/2, 150)
        screen.blit(text, text_rect)

        draw_network(screen)

        if len(mountains) == 0:
            screen.blit(goal_image, (goal_position, screen_height - 400))

        pygame.display.flip()
        clock.tick(60)

def run_car(genomes, config):
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    generation_font = pygame.font.SysFont("Arial", 70)
    font = pygame.font.SysFont("Arial", 30)
    goal_position = screen_width
    goal_image = pygame.image.load("goal.png")

    global space
    space = pymunk.Space()
    space.gravity = (0.0, -900.0)

    add_land(space)
    mountains = add_mountatins(space)

    distances = []
    for i, m in enumerate(mountains):
        distances.append([m[0].position.x, i])
    distances.append([999999, 51])
    #distances.append([distances[-1][1][0].position.x + 2000, 51])

    nets = []
    ge = []
    cars = []

    for id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        cars.append(Car())
        g.fitness = 0
        ge.append(g)

    #main game
    global generation
    generation += 1
    dist = 10
    dist_at = 0
    dist_x = screen_width
    dist_flag = True
    time = 0
    global best_fitness
    global show_cnt
    global show_flag
    if best_fitness > 1000:
        show_cnt += 1
    else:
        show_cnt = 0

    best_fitness = 0
    show_flag = True
    #if show_cnt >= 5:
    #    show_flag = True
    #else:
    #    show_flag = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # check
        if len(cars) == 0:
            mountains.clear()
            break

        for index, car in enumerate(cars):
            output = nets[index].activate(car.get_data(screen))
            out = max(output)
            i = output.index(max(output))
            #for i, out in enumerate(output):
            if out > 0.5:
                if i == 0:
                    car.speed -= 3

        maximum = 0
        at = 0
        if show_flag:
            space.step(0.02)
        else:
            space.step(0.05)
        for i, car in enumerate(cars):
            car.update()
            car.set_colors()
            if car.body.position.x > maximum:
                at = i
                maximum = car.body.position.x

        #print(nets[index].activate(cars[at].get_data(screen)))
        cars[at].set_colors(body_color = (0, 0, 0), human_color = (255, 0, 0), wheel_color = (100, 100, 100))
        if cars[at].body.position.x > screen_width / 2 or cars[at].body.position.x < 0:
            d = cars[at].body.position.x - screen_width / 2
            for i, car in enumerate(cars):
                car.set_position(d)

            for i, m in enumerate(mountains):
                m[0]._set_position((m[0].position.x - d, m[0].position.y))

            if cars[at].check >= 49:
                goal_position -= d

            for dis in distances:
                dis[0] -= d

        for i, m in enumerate(mountains):
            if m[0].position.x < screen_width and m[2] == False:
                m[2] = True
                space.add(m[0], m[1])

            #if m[0].position.x < -3000 and m[2] == True:
                #space.remove(m[0], m[1])
                #mountains.remove(m)

        #drawing
        if show_flag:
            screen.fill((255, 255, 255))
            space.debug_draw(draw_options)
            cars[at].draw_image(screen)


            for i in [-100, 0, 100, 300, 500]:
                x = cars[at].body.position.x + i
                if x < 0:
                    x = 0
                for i in range(screen_height-1, 0, -1):
                    if screen.get_at((int(x), int(i))) != (39, 174, 96, 255):
                        pygame.draw.circle(screen, (0, 0, 0), (int(x), int(i)), 5)
                        break

            text = generation_font.render("Generation : " + str(generation), True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (screen_width/2, 100)
            screen.blit(text, text_rect)

            text = font.render("Best fitness : " + str(int(ge[at].fitness)), True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (screen_width*3/4, 100)
            screen.blit(text, text_rect)

            text = font.render("remain cars : " + str(int(len(cars))), True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (screen_width*3/4, 150)
            screen.blit(text, text_rect)

            for d in distances:
                if d[0] > 0 and d[0] < screen_width:
                    text = generation_font.render(str(d[1]), True, (0, 0, 0))
                    text_rect = text.get_rect()
                    text_rect.center = (d[0], 300)
                    screen.blit(text, text_rect)


            if cars[at].check >= 49:
                screen.blit(goal_image, (goal_position, screen_height - 400))

        for i, car in enumerate(cars):
            if distances[car.check][0] - car.body.position.x < car.prev_dist:
                if car.body.position.x > distances[car.check][0]:
                    #ge[i].fitness += 1
                    car.check += 1

            car.prev_dist = distances[car.check][0] - car.body.position.x

            if ge[i].fitness > best_fitness:
                best_fitness = ge[i].fitness

            angle = math.degrees(car.body.angle) % 360
            #ge[i].fitness += 0.1
            if angle < 60:
                ge[i].fitness += 0.1

            #if car.check >= 50:
            if car.body.position.x > goal_position:
                ge[i].fitness += 1000
                if ge[i].fitness > best_fitness:
                    best_fitness = ge[i].fitness
                space.remove(car.get_shapes())
                cars.remove(car)
                ge.pop(i)
            elif car.is_dead:
                ge[i].fitness -= 100
                space.remove(car.get_shapes())
                cars.remove(car)
                ge.pop(i)

        pygame.display.flip()
        if show_flag:
            clock.tick(60)
        else:
            clock.tick(0)

#run_test()

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    generation = 0
    winner = p.run(run_car, 1000)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
