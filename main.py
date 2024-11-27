import pygame
import random
import math

# Game constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
PLAYER_SIZE = (90, 90)
BULLET_SIZE = (20, 20)
SHIELD_DURATION = 600  # In frames (10 seconds at 60 FPS)
SHIELD_COST = 1
ENEMY_SIZE = (70, 70)
ENEMY_HEALTH = 2
PARTICLE_COUNT = 20
PARTICLE_SIZE = 4
PARTICLE_SPEED_RANGE = (2, 5)
STAR_COUNT = 100
STAR_SIZE_RANGE = (0.5, 2)
STAR_SPEED_RANGE = (0.5, 2)
WAVE_SPAWN_DELAY = 180  # In frames (3 seconds at 60 FPS)

# Colors
BACKGROUND_COLOR = (0, 0, 0)  # Full black background
STAR_COLOR = (255, 255, 255)


class SpaceWars:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Space Wars")

        # Load all ship images
        self.player_images = [
            pygame.transform.scale(pygame.image.load("player_ship.png"), PLAYER_SIZE),
            pygame.transform.scale(pygame.image.load("player_ship_2.png"), PLAYER_SIZE),
            pygame.transform.scale(pygame.image.load("player_ship_3.png"), PLAYER_SIZE)
        ]

        self.enemy_images = [
            pygame.transform.scale(pygame.image.load("enemy_ship.png"), ENEMY_SIZE),
            pygame.transform.scale(pygame.image.load("enemy_ship_2.png"), ENEMY_SIZE),
            pygame.transform.scale(pygame.image.load("enemy_ship_3.png"), ENEMY_SIZE)
        ]

        self.bullet_image = pygame.transform.scale(pygame.image.load("bullet.png"), BULLET_SIZE)

        # Load trophy images for different waves
        self.trophy_images = [
            pygame.transform.scale(pygame.image.load("trophy1.png"), (90, 90)),
            pygame.transform.scale(pygame.image.load("trophy2.png"), (90, 90)),
            pygame.transform.scale(pygame.image.load("trophy3.png"), (90, 90))
        ]

        self.current_player_image = 0
        self.current_enemy_image = 0

        self.player_image = self.player_images[self.current_player_image]
        self.enemy_image = self.enemy_images[self.current_enemy_image]

        self.player_pos = [WINDOW_WIDTH // 2, WINDOW_HEIGHT - PLAYER_SIZE[1]]
        self.player_shield = 100
        self.shield_segments = []
        self.bullets = []
        self.enemies = []
        self.stars = self.generate_stars(STAR_COUNT)

        self.particles = []
        self.shield_particles = []

        self.score = 0
        self.wave = 1
        self.game_over = False
        self.wave_cleared = False

        self.can_shoot = True
        self.shoot_cooldown = 0
        self.shoot_delay = 10

        self.building_shield = False
        self.last_shield_pos = None

        self.font = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()
        self.wave_timer = 0

        # Trophy display state
        self.show_trophies = False
        self.trophy_timer = 0
        self.trophy_display_duration = 120  # 2 seconds at 60 FPS

    def generate_stars(self, num_stars):
        return [
            {
                'pos': [random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT)],
                'size': random.uniform(*STAR_SIZE_RANGE),
                'speed': random.uniform(*STAR_SPEED_RANGE)
            } for _ in range(num_stars)
        ]

    def spawn_wave(self):
        num_enemies = 5 + self.wave * 2

        # Cycle through player and enemy images
        self.current_player_image = (self.wave - 1) % len(self.player_images)
        self.current_enemy_image = (self.wave - 1) % len(self.enemy_images)

        self.player_image = self.player_images[self.current_player_image]
        self.enemy_image = self.enemy_images[self.current_enemy_image]

        self.enemies = [
            {
                'pos': [random.randint(ENEMY_SIZE[0] // 2, WINDOW_WIDTH - ENEMY_SIZE[0] // 2),
                        random.randint(-ENEMY_SIZE[1], -ENEMY_SIZE[1] // 2)],
                'vel': [random.uniform(-1, 1), random.uniform(0.5, 1.5)],
                'size': ENEMY_SIZE,
                'health': ENEMY_HEALTH
            } for _ in range(num_enemies)
        ]

        self.wave += 1
        self.wave_cleared = False

    def add_particles(self, pos, color):
        self.particles.extend([
            {
                'pos': list(pos),
                'vel': [math.cos(random.uniform(0, 2 * math.pi)) * random.uniform(*PARTICLE_SPEED_RANGE),
                        math.sin(random.uniform(0, 2 * math.pi)) * random.uniform(*PARTICLE_SPEED_RANGE)],
                'timer': 1.0,
                'color': color
            } for _ in range(PARTICLE_COUNT)
        ])

    def update_particles(self):
        self.particles = [
            particle for particle in self.particles
            if particle['timer'] > 0
        ]
        for particle in self.particles:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['timer'] -= 0.02

    def update_stars(self):
        for star in self.stars:
            star['pos'][1] += star['speed']
            if star['pos'][1] > WINDOW_HEIGHT:
                star['pos'][1] = 0
                star['pos'][0] = random.randint(0, WINDOW_WIDTH)

    def check_collisions(self):
        # Bullet-enemy collisions
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                dx = bullet['pos'][0] - enemy['pos'][0]
                dy = bullet['pos'][1] - enemy['pos'][1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < max(enemy['size']) / 2:
                    enemy['health'] -= 1
                    if enemy['health'] <= 0:
                        self.enemies.remove(enemy)
                        self.score += 100
                        self.add_particles(enemy['pos'], (255, 50, 50))
                    self.bullets.remove(bullet)
                    break

        # Enemy-player collisions
        for enemy in self.enemies:
            dx = self.player_pos[0] - enemy['pos'][0]
            dy = self.player_pos[1] - enemy['pos'][1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < max(PLAYER_SIZE) / 2 + max(enemy['size']) / 2:
                self.game_over = True

    def update(self, delta_time):
        if not self.game_over:
            self.player_pos[0] = pygame.mouse.get_pos()[0]
            self.player_pos[0] = max(PLAYER_SIZE[0] // 2, min(WINDOW_WIDTH - PLAYER_SIZE[0] // 2, self.player_pos[0]))

            for bullet in self.bullets[:]:
                bullet['pos'][1] -= 10
                if bullet['pos'][1] < 0:
                    self.bullets.remove(bullet)

            for enemy in self.enemies:
                enemy['pos'][0] += enemy['vel'][0]
                enemy['pos'][1] += enemy['vel'][1]

                if enemy['pos'][0] < enemy['size'][0] // 2 or enemy['pos'][0] > WINDOW_WIDTH - enemy['size'][0] // 2:
                    enemy['vel'][0] *= -1

                if enemy['pos'][1] > WINDOW_HEIGHT:
                    self.game_over = True

            if not self.can_shoot:
                self.shoot_cooldown += 1
                if self.shoot_cooldown >= self.shoot_delay:
                    self.can_shoot = True
                    self.shoot_cooldown = 0

            self.update_particles()
            self.update_stars()
            self.check_collisions()

            if len(self.enemies) == 0 and not self.wave_cleared:
                self.wave_cleared = True
                self.wave_timer = WAVE_SPAWN_DELAY

                # Show trophies based on the current wave
                self.show_trophies = True
                self.trophy_timer = self.trophy_display_duration

            if self.wave_cleared and self.trophy_timer > 0:
                self.trophy_timer -= 1
                if self.trophy_timer <= 0:
                    self.show_trophies = False

            if self.wave_cleared:
                self.wave_timer -= 1
                if self.wave_timer <= 0:
                    self.spawn_wave()

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        for star in self.stars:
            pygame.draw.circle(self.screen, STAR_COLOR,
                               (int(star['pos'][0]), int(star['pos'][1])), int(star['size']))

        # Draw player
        self.screen.blit(self.player_image, (self.player_pos[0] - PLAYER_SIZE[0] // 2, self.player_pos[1]))

        # Draw bullets
        for bullet in self.bullets:
            self.screen.blit(self.bullet_image, (bullet['pos'][0] - BULLET_SIZE[0] // 2, bullet['pos'][1]))

        # Draw enemies
        for enemy in self.enemies:
            self.screen.blit(self.enemy_image, (enemy['pos'][0] - enemy['size'][0] // 2, enemy['pos'][1]))

        # Draw particles
        for particle in self.particles:
            color = particle['color']
            pygame.draw.circle(self.screen, color, (int(particle['pos'][0]), int(particle['pos'][1])), PARTICLE_SIZE)

        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        # Draw trophies
        if self.show_trophies and self.wave > 1:
            trophy_index = (self.wave - 2) % len(self.trophy_images)
            self.screen.blit(self.trophy_images[trophy_index], (WINDOW_WIDTH // 2 - 30, WINDOW_HEIGHT // 2 - 30))

        # Draw game over message
        if self.game_over:
            game_over_text = self.font.render("GAME OVER!", True, (255, 0, 0))
            self.screen.blit(game_over_text, (WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 20))

        pygame.display.flip()

    def run(self):
        self.spawn_wave()
        running = True

        while running:
            delta_time = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.can_shoot and not self.game_over:
                        self.bullets.append({
                            'pos': [self.player_pos[0], self.player_pos[1] - PLAYER_SIZE[1] // 2],
                            'size': BULLET_SIZE
                        })
                        self.can_shoot = False

            self.update(delta_time)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    game = SpaceWars()
    game.run()
