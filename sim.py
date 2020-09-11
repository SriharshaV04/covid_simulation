import pygame
import numpy as np


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255) #uninfected
GREEN = (50, 150, 50) #infected
PURPLE = (130, 0, 130) # Recovered
YELLOW = (190, 175, 50)

BACKGROUND = WHITE


class Dot(pygame.sprite.Sprite):
    def __init__(
        self,
        x,
        y,
        width,
        height,
        color=BLACK,
        radius=5,
        velocity=[0,0],
        randomize=False,
    ):
        super().__init__()
        self.image = pygame.Surface([radius * 2, radius * 2])
        self.image.fill(BACKGROUND)
        pygame.draw.circle(
            self.image, color, (radius, radius), radius
        )

        self.rect = self.image.get_rect()
        self.pos = np.array([x, y], dtype=np.float64)
        self.vel = np.asarray(velocity, dtype=np.float64)

        self.killswitch_on = False
        self.recovered = False
        self.dead = False
        self.randomize = randomize

        self.WIDTH = width
        self.HEIGHT = height

    def update(self):

        self.pos += self.vel

        x, y = self.pos

        # Periodic boundary conditions
        if x < 0:
            self.pos[0] = self.WIDTH
            x = self.WIDTH
        if x > self.WIDTH:
            self.pos[0] = 0
            x = 0
        if y < 0:
            self.pos[1] = self.HEIGHT
            y = self.HEIGHT
        if y > self.HEIGHT:
            self.pos[1] = 0
            y = 0

        self.rect.x = x
        self.rect.y = y

        vel_norm = np.linalg.norm(self.vel)
        if vel_norm > 3:
            self.vel /= vel_norm

        if self.randomize:
            self.vel += np.random.rand(2) * 2 - 1

        if self.killswitch_on:
            self.cycles_to_fate -= 1

            if self.cycles_to_fate <= 0:
                self.killswitch_on = False
                some_number = np.random.rand()
                if self.mortality_rate > some_number:
                    self.kill()
                    self.dead = True
                else:
                    self.recovered = True

    def respawn(self,color):
        return Dot(
            self.rect.x,
            self.rect.y,
            self.WIDTH,
            self.HEIGHT,
            color=color,
            velocity=self.vel
        )

    def killswitch(self, cycles_to_fate=20, mortality_rate=0.2):
        self.killswitch_on = True
        self.cycles_to_fate = cycles_to_fate
        self.mortality_rate = mortality_rate


class Simulation:
    def __init__(self, width=600, height=480):
        self.WIDTH = width
        self.HEIGHT = height

        self.susceptible_container = pygame.sprite.Group()
        self.infected_container = pygame.sprite.Group()
        self.recovered_container = pygame.sprite.Group()
        self.dead_container = pygame.sprite.Group()
        self.all_container = pygame.sprite.Group()

        self.n_susceptible = 20
        self.n_infected = 1
        self.n_quarantined = 0
        self.cycles_to_fate = 20
        self.mortality_rate = 0.2

    def start(self, randomize=False):

        self.N = (
            self.n_susceptible + self.n_infected + self.n_quarantined
        )

        pygame.init()
        screen = pygame.display.set_mode([self.WIDTH, self.HEIGHT])
        days =0
        f = 0

        for i in range(self.n_susceptible):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.HEIGHT + 1)
            guy = Dot(
                x,
                y,
                self.WIDTH,
                self.HEIGHT,
                color=BLUE,
                velocity=[0,0],
                randomize=randomize,
            )
            self.susceptible_container.add(guy)
            self.all_container.add(guy)

        for i in range(self.n_quarantined):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.HEIGHT + 1)
            vel = np.random.rand(2) * 2 - 1
            guy = Dot(
                x,
                y,
                self.WIDTH,
                self.HEIGHT,
                color=BLUE,
                velocity=vel,
                randomize=False,
            )
            self.susceptible_container.add(guy)
            self.all_container.add(guy)

        for i in range(self.n_infected):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.HEIGHT + 1)
            vel = np.random.rand(2) * 2 - 1
            guy = Dot(
                x,
                y,
                self.WIDTH,
                self.HEIGHT,
                color=GREEN,
                velocity=vel,
                randomize=randomize,
            )
            self.infected_container.add(guy)
            self.all_container.add(guy)

        self.font = pygame.font.SysFont(None, 20, True)


        clock = pygame.time.Clock()
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False


            self.all_container.update()

            screen.fill(BACKGROUND)

            # New infections?
            collision_group = pygame.sprite.groupcollide(
                self.susceptible_container,
                self.infected_container,
                True, # remove from susceptible container
                False, # don't remove
            )

            infections=0
            for guy in collision_group:
                new_guy = guy.respawn(GREEN)
                new_guy.vel *= -1
                new_guy.killswitch(
                    self.cycles_to_fate, self.mortality_rate
                )
                self.infected_container.add(new_guy)
                self.all_container.add(new_guy)
                infections+=1

            # Any recoveries?
            recovered = []
            for guy in self.infected_container:
                if guy.recovered:
                    new_guy = guy.respawn(PURPLE)
                    self.recovered_container.add(new_guy)
                    self.all_container.add(new_guy)
                    recovered.append(guy)

            if len(recovered) > 0:
                self.infected_container.remove(*recovered)
                self.all_container.remove(*recovered)

            # Dead
            deaths = []
            for guy in self.infected_container:
                if guy.dead:
                    new_guy = guy.respawn(YELLOW)
                    self.all_container.add(new_guy)
                    self.dead_container.add(new_guy)
                    deaths.append(new_guy)

            if len(deaths) > 0:
                self.infected_container.remove(*deaths)
                self.all_container.remove(*deaths)

            f+=1
            if f % 8 == 0:
                days+=1

            self.all_container.draw(screen)
            initial_total = self.n_infected+ self.n_quarantined+self.n_susceptible
            self.text = self.font.render("DAYS: " + str(days), False, BLACK)
            screen.blit(self.text, (self.WIDTH // 40, (self.HEIGHT // 40)))
            self.text = self.font.render("UNINFECTED: " + str(len(self.susceptible_container)),False, BLUE)
            screen.blit(self.text, (self.WIDTH // 40, (self.HEIGHT // 40)+20))
            self.text = self.font.render("INFECTED: " + str(len(self.infected_container)), True, GREEN)
            screen.blit(self.text, (self.WIDTH // 40, (self.HEIGHT // 40)+40))
            self.text = self.font.render("RECOVERED: " + str(len(self.recovered_container)), True, PURPLE)
            screen.blit(self.text, (self.WIDTH // 40, (self.HEIGHT // 40)+60))
            self.text = self.font.render("DEAD: " + str(initial_total-len(self.recovered_container)
                                                        -len(self.infected_container)
                                                        -len(self.susceptible_container)), True, YELLOW)
            screen.blit(self.text, (self.WIDTH // 40, (self.HEIGHT // 40)+80))
            pygame.display.flip()

            clock.tick(30)

        pygame.quit()


covid = Simulation(600, 480)
covid.n_susceptible = 95
covid.n_infected = 5
covid.cycles_to_fate = 200
covid.mortality_rate = 0.03
keys = pygame.key.get_pressed

covid.start(randomize=True)
