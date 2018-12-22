import pygame
import sys
import time
import random
import math
import cv2 as cv
import numpy as np
from pygame.locals import *

FPS = 30
pygame.init()
fpsClock=pygame.time.Clock()

SCREEN_WIDTH, SCREEN_HEIGHT = 600, 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
surface = pygame.Surface(screen.get_size())
surface = surface.convert()
pygame.key.set_repeat(1, 40)
myfont = pygame.font.Font('font.ttf', 60)

class Ball(object):
    INIT_BALL_SPEED = 200
    BALL_DIRS = ((1, 1), (-1, 1), (-1, -1), (1, -1))

    def __init__(self, radius=30):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.radius = radius
        self.speed = self.INIT_BALL_SPEED
        self.vx = 1
        self.vy = 1
        self.latest_goal = 1
        self.image = pygame.image.load('ball.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (int(radius*2.2), int(radius*2.2)))

        self.bounceTimer = 0.0
        self.readyTimer = 2.0

    def check_collision(self, game):
        SPEED_INC = 1.2

        if self.y + self.radius > SCREEN_HEIGHT or self.y - self.radius < 0:
            self.vy *= -1

        if self.bounceTimer > 0.3 and game.sframe[int(self.x), int(self.y)] > 0:
            self.speed = self.speed * SPEED_INC
            self.bounceTimer = 0

            self.vx *= -1
            angle = random.uniform(-math.pi/9, +math.pi/9)

        self.speed = min(self.speed, 500)

    def check_goal(self):
        if self.x - self.radius > SCREEN_WIDTH:
            self.latest_goal = 1
            return 1
        elif self.x + self.radius < 0:
            self.latest_goal = -1
            return -1
        else:
            return 0

    def reset(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.speed = self.INIT_BALL_SPEED
        self.vx = 1 if self.latest_goal == 1 else -1
        self.vy = random.choice([1, -1])
        self.bounceTimer = 0
        self.readyTimer = 2.0

    def move(self, vx, vy, dt):
        if self.readyTimer > 0.0:
            return

        self.x += self.speed * vx * dt
        self.y += self.speed * vy * dt

    def update(self, dt, game):
        self.bounceTimer += dt
        self.readyTimer -= dt

        self.check_collision(game)
        self.move(self.vx, self.vy, dt)

    def draw(self):
        # pygame.draw.circle(surface, (0, 255, 0), (int(self.x), int(self.y)), self.radius)
        surface.blit(self.image, (int(self.x-self.radius), int(self.y-self.radius)))

class PongGame(object):
    def __init__(self):
        self.ball = Ball()

        self.capture = cv.VideoCapture(0)
        self.capture.set(cv.CAP_PROP_FPS, 25);
        self.capture.set(cv.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
        self.capture.set(cv.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)

        self.sframe = None # binary skin frame
        self.frame = None

        self.scoreA = 0
        self.scoreB = 0

        self.showSFrame = False

    def update(self, dt):
        _, self.frame = self.capture.read()
        self.frame = np.rot90(self.frame)

        Y, Cr, Cb = cv.split(cv.cvtColor(self.frame, cv.COLOR_BGR2YCrCb))
        B, G, R = cv.split(self.frame)
        self.frame = cv.merge([R, G, B])

        Cr = cv.inRange(Cr, 134, 165)
        Cb = cv.inRange(Cb, 102, 116)
        self.sframe = cv.inRange(cv.blur(cv.bitwise_and(Cr, Cb), (20, 20)), 200, 255)
        self.sframe[150:SCREEN_WIDTH-150, 0:SCREEN_HEIGHT] = 0

        self.ball.update(dt, self)

        goal = self.ball.check_goal()
        if goal == 1:
            self.scoreA += 1
            self.ball.reset()
        elif goal == -1:
            self.scoreB += 1
            self.ball.reset()

    def draw(self):
        if self.showSFrame:
            surface.blit(
                pygame.surfarray.make_surface(cv.merge([self.sframe, self.sframe, self.sframe])),
                (0, 0)
            )
        else:
            surface.blit(
                pygame.surfarray.make_surface(self.frame),
                (0, 0)
            )

        # draw line
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect((150, 0), (5, SCREEN_HEIGHT)))
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect((SCREEN_WIDTH-150-5, 0), (5, SCREEN_HEIGHT)))

        self.ball.draw()

        scoreA_sf = myfont.render(str(self.scoreA), True, (255, 0, 0))
        surface.blit(scoreA_sf,(SCREEN_WIDTH/2-scoreA_sf.get_width()-50,SCREEN_HEIGHT/2))

        scoreB_sf = myfont.render(str(self.scoreB), True, (0, 255, 0))
        surface.blit(scoreB_sf,(SCREEN_WIDTH/2+50, SCREEN_HEIGHT/2))

if __name__ == "__main__":
    game = PongGame()

    while True:
        game.update(1./FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == K_t:
                game.showSFrame = not game.showSFrame

        surface.fill((0, 0, 0))
        game.draw()
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        pygame.display.update()

        fpsClock.tick(FPS)

