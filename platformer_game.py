import pygame
import sys
import math
import time
import os
import random
import colorsys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5

# Enemy constants
BEE_ATTACK_RANGE = 300
BEE_PROJECTILE_SPEED = 5
BEE_FIRE_COOLDOWN = 100  # frames (about 1.5 seconds at 60 FPS)

# Level constants
MAX_LEVELS = 5
LEVEL_COMPLETE_DELAY = 180  # 3 seconds at 60 FPS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)  # Platform rengi için gri
LIGHT_GRAY = (192, 192, 192)  # Açık gri
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.health = 100
        self.max_health = 100
        self.invulnerable_time = 0  # Add invulnerability frames after taking damage
        
        # Animation properties
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 8  # Frames between animation changes
        self.facing_right = True
        self.is_jumping = False
        self.is_moving = False
        
        # Load player sprite
        try:
            self.original_image = pygame.image.load("assets/player.png").convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (self.width, self.height))
            self.image = self.original_image.copy()
        except pygame.error:
            # Fallback to colored rectangle if image not found
            self.original_image = pygame.Surface((self.width, self.height))
            self.original_image.fill(BLUE)
            self.image = self.original_image.copy()
            print("Warning: player.png not found, using colored rectangle")
    
    def update(self, platforms):
        # Handle input
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        self.is_moving = False
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
            self.is_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
            self.is_moving = True
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            self.is_jumping = True
        
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Update invulnerability
        if self.invulnerable_time > 0:
            self.invulnerable_time -= 1
        
        # Update animation
        self.update_animation()
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Update rect
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Check boundaries
        if self.x < 0:
            self.x = 0
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        
        # Ground collision (bottom of screen)
        if self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height
            self.vel_y = 0
            self.on_ground = True
            self.is_jumping = False
        
        # Platform collision
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Landing on top of platform
                if self.vel_y > 0 and self.y < platform.y:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                    self.is_jumping = False
                # Hitting platform from below
                elif self.vel_y < 0 and self.y > platform.y:
                    self.y = platform.y + platform.height
                    self.vel_y = 0
                # Side collisions
                elif self.vel_x > 0:  # Moving right
                    self.x = platform.x - self.width
                elif self.vel_x < 0:  # Moving left
                    self.x = platform.x + platform.width
        
        # Update rect after collision detection
        self.rect.x = self.x
        self.rect.y = self.y
    
    def update_animation(self):
        """Update player animation based on state"""
        self.animation_timer += 1
        
        # Create base image
        current_image = self.original_image.copy()
        
        # Apply different effects based on player state
        if self.is_jumping:
            # Jumping animation - slight rotation
            angle = math.sin(self.animation_timer * 0.3) * 5
            current_image = pygame.transform.rotate(current_image, angle)
        elif self.is_moving:
            # Walking animation - slight bounce
            if self.animation_timer % self.animation_speed < self.animation_speed // 2:
                # Compress slightly when walking
                current_image = pygame.transform.scale(current_image, (self.width, self.height - 2))
            # Add slight tilt when moving
            tilt = 3 if self.facing_right else -3
            current_image = pygame.transform.rotate(current_image, tilt)
        else:
            # Idle animation - gentle breathing effect
            scale_factor = 1 + math.sin(self.animation_timer * 0.1) * 0.02
            new_width = int(self.width * scale_factor)
            new_height = int(self.height * scale_factor)
            current_image = pygame.transform.scale(current_image, (new_width, new_height))
        
        # Flip image if facing left
        if not self.facing_right:
            current_image = pygame.transform.flip(current_image, True, False)
        
        # Apply invulnerability flashing
        if self.invulnerable_time > 0 and self.invulnerable_time % 10 < 5:
            # Create flashing effect by adjusting alpha
            flash_surface = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, 100))
            current_image.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        self.image = current_image
    
    def take_damage(self, amount):
        """Handle player taking damage"""
        if self.invulnerable_time <= 0:  # Only take damage if not invulnerable
            self.health -= amount
            self.invulnerable_time = 60  # 1 second of invulnerability at 60 FPS
            print(f"Player hit by Stinger! Health: {self.health}")
            if self.health <= 0:
                self.health = 0
                return True  # Return True to indicate game over
        return False
    
    def reset_health(self):
        """Reset player health for new level"""
        self.health = self.max_health
        self.invulnerable_time = 0
    
    def draw(self, screen):
        # Draw player sprite (animation is handled in update_animation)
        screen.blit(self.image, (self.x, self.y))
        
        # Draw health bar
        health_bar_width = 50
        health_bar_height = 6
        health_percentage = self.health / self.max_health
        
        # Background (red)
        pygame.draw.rect(screen, RED, 
                        (self.x - 5, self.y - 15, health_bar_width, health_bar_height))
        # Health (green)
        pygame.draw.rect(screen, GREEN, 
                        (self.x - 5, self.y - 15, health_bar_width * health_percentage, health_bar_height))

class Stinger(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, speed):
        super().__init__()
        self.x = x
        self.y = y
        self.speed = speed
        
        # Animation properties
        self.rotation_angle = 0
        self.trail_positions = []  # For trail effect
        self.animation_timer = 0
        
        # Calculate direction to target
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.vel_x = (dx / distance) * speed
            self.vel_y = (dy / distance) * speed
            # Calculate initial rotation based on direction
            self.base_angle = math.degrees(math.atan2(dy, dx))
        else:
            self.vel_x = 0
            self.vel_y = 0
            self.base_angle = 0
        
        # Load stinger sprite
        try:
            self.original_image = pygame.image.load("assets/stinger.png").convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (20, 8))
        except pygame.error:
            # Fallback to colored rectangle if image not found
            self.original_image = pygame.Surface((8, 3))
            self.original_image.fill(BLACK)
            print("Warning: stinger.png not found, using colored rectangle")
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
    
    def update(self):
        """Update stinger position and animation"""
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Update animation
        self.update_animation()
        
        # Update trail positions
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 8:  # Keep last 8 positions for trail
            self.trail_positions.pop(0)
        
        self.rect.center = (self.x, self.y)
        
        # Remove if off screen
        if (self.x < -50 or self.x > SCREEN_WIDTH + 50 or 
            self.y < -50 or self.y > SCREEN_HEIGHT + 50):
            self.kill()
    
    def update_animation(self):
        """Update stinger animation"""
        self.animation_timer += 1
        
        # Spinning animation
        self.rotation_angle = (self.base_angle + self.animation_timer * 10) % 360
        
        # Rotate the image
        self.image = pygame.transform.rotate(self.original_image, self.rotation_angle)
        
        # Pulsing effect
        pulse = math.sin(self.animation_timer * 0.3) * 0.1 + 1
        pulse_width = int(self.original_image.get_width() * pulse)
        pulse_height = int(self.original_image.get_height() * pulse)
        self.image = pygame.transform.scale(self.image, (pulse_width, pulse_height))
    
    def draw(self, screen):
        """Draw the stinger projectile with trail effect"""
        # Draw trail
        for i, pos in enumerate(self.trail_positions):
            if i < len(self.trail_positions) - 1:  # Don't draw trail at current position
                alpha = int(255 * (i / len(self.trail_positions)) * 0.5)
                trail_color = (*YELLOW, alpha) if alpha > 0 else YELLOW
                trail_size = max(1, int(3 * (i / len(self.trail_positions))))
                
                # Create a surface for the trail dot with alpha
                trail_surface = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, (*YELLOW, alpha), (trail_size, trail_size), trail_size)
                screen.blit(trail_surface, (pos[0] - trail_size, pos[1] - trail_size))
        
        # Draw main stinger
        screen.blit(self.image, self.rect)

class HiveGuardBee(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.attack_range = BEE_ATTACK_RANGE
        self.projectile_speed = BEE_PROJECTILE_SPEED
        self.fire_cooldown = 0
        self.max_fire_cooldown = BEE_FIRE_COOLDOWN
        
        # Animation properties
        self.animation_frame = 0
        self.animation_timer = 0
        self.wing_flap_speed = 4  # Faster wing flapping
        self.hover_offset = 0
        self.is_attacking = False
        self.attack_animation_timer = 0
        
        # Load bee sprite
        try:
            self.original_image = pygame.image.load("assets/bee.png").convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (self.width, self.height))
            self.image = self.original_image.copy()
        except pygame.error:
            # Fallback to colored rectangle if image not found
            self.original_image = pygame.Surface((self.width, self.height))
            self.original_image.fill(YELLOW)
            self.image = self.original_image.copy()
            print("Warning: bee.png not found, using colored rectangle")
        
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self, player, stinger_group):
        """Update bee behavior"""
        # Reduce fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        
        # Update animation
        self.update_animation()
        
        # Check if player is in range
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        bee_center_x = self.x + self.width // 2
        bee_center_y = self.y + self.height // 2
        
        distance = math.sqrt((player_center_x - bee_center_x)**2 + 
                           (player_center_y - bee_center_y)**2)
        
        # Fire at player if in range and cooldown is ready
        if distance <= self.attack_range and self.fire_cooldown <= 0:
            stinger = Stinger(bee_center_x, bee_center_y, 
                            player_center_x, player_center_y, 
                            self.projectile_speed)
            stinger_group.add(stinger)
            self.fire_cooldown = self.max_fire_cooldown
            self.is_attacking = True
            self.attack_animation_timer = 20  # Attack animation duration
        
        # Update attack animation timer
        if self.attack_animation_timer > 0:
            self.attack_animation_timer -= 1
            if self.attack_animation_timer == 0:
                self.is_attacking = False
    
    def update_animation(self):
        """Update bee animation"""
        self.animation_timer += 1
        
        # Create base image
        current_image = self.original_image.copy()
        
        # Hovering animation - gentle up and down movement
        self.hover_offset += 0.15
        hover_y = math.sin(self.hover_offset) * 3
        
        # Wing flapping effect - slight scale change
        wing_flap = math.sin(self.animation_timer * 0.5) * 0.1 + 1
        flap_width = int(self.width * wing_flap)
        flap_height = int(self.height * (2 - wing_flap) * 0.5 + self.height * 0.5)
        current_image = pygame.transform.scale(current_image, (flap_width, flap_height))
        
        # Attack animation - red tint and slight enlargement
        if self.is_attacking:
            attack_scale = 1.2
            current_image = pygame.transform.scale(current_image, 
                                                 (int(self.width * attack_scale), 
                                                  int(self.height * attack_scale)))
            # Add red tint
            red_tint = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
            red_tint.fill((255, 100, 100, 100))
            current_image.blit(red_tint, (0, 0), special_flags=pygame.BLEND_ADD)
        
        self.image = current_image
        
        # Update rect position with hover effect
        self.rect.y = self.y + hover_y
    
    def draw(self, screen):
        """Draw the hive guard bee"""
        # Draw bee sprite
        screen.blit(self.image, (self.x, self.y))
        
        # Draw attack range indicator (faint circle when debugging)
        # pygame.draw.circle(screen, (255, 255, 0, 50), 
        #                  (self.x + self.width // 2, self.y + self.height // 2), 
        #                  self.attack_range, 1)

class DreamEssence(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        
        # Animation properties
        self.float_offset = 0
        self.animation_timer = 0
        self.sparkle_timer = 0
        self.color_shift = 0
        self.pulse_scale = 1.0
        
        # Load dream essence sprite
        try:
            self.original_image = pygame.image.load("assets/dreamessence.png").convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (self.width, self.height))
        except pygame.error:
            # Fallback to colored circle if image not found
            self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, CYAN, (self.width//2, self.height//2), self.width//2)
            print("Warning: dreamessence.png not found, using colored circle")
        
        self.image = self.original_image.copy()
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self):
        """Update dream essence with enhanced floating animation"""
        self.animation_timer += 1
        
        # Floating animation - more complex movement
        self.float_offset += 0.08
        float_y = math.sin(self.float_offset) * 8 + math.sin(self.float_offset * 2) * 3
        
        # Update animation
        self.update_animation()
        
        # Update rect position with float effect
        self.rect.y = self.y + float_y
    
    def update_animation(self):
        """Update dream essence visual effects"""
        # Color shifting effect
        self.color_shift += 0.1
        
        # Pulsing scale effect
        self.pulse_scale = 1.0 + math.sin(self.animation_timer * 0.15) * 0.2
        
        # Create base image with scaling
        scaled_width = int(self.width * self.pulse_scale)
        scaled_height = int(self.height * self.pulse_scale)
        current_image = pygame.transform.scale(self.original_image, (scaled_width, scaled_height))
        
        # Add color tint cycling through rainbow colors
        hue = (self.color_shift * 50) % 360
        # Convert HSV to RGB for color cycling
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.7, 1.0)
        tint_color = (int(r * 255), int(g * 255), int(b * 255), 100)
        
        # Apply color tint
        tint_surface = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
        tint_surface.fill(tint_color)
        current_image.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # Add glow effect
        glow_intensity = math.sin(self.animation_timer * 0.2) * 0.5 + 0.5
        glow_surface = pygame.Surface(current_image.get_size(), pygame.SRCALPHA)
        glow_surface.fill((255, 255, 255, int(50 * glow_intensity)))
        current_image.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        self.image = current_image
    
    def draw(self, screen):
        """Draw the dream essence with sparkle effects"""
        # Draw sparkles around the essence
        self.sparkle_timer += 1
        if self.sparkle_timer % 10 == 0:  # Create sparkles every 10 frames
            for _ in range(3):
                sparkle_x = self.rect.centerx + random.randint(-25, 25)
                sparkle_y = self.rect.centery + random.randint(-25, 25)
                sparkle_size = random.randint(1, 3)
                sparkle_color = (255, 255, 255, 150)
                
                # Draw sparkle
                sparkle_surface = pygame.Surface((sparkle_size * 2, sparkle_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surface, sparkle_color, (sparkle_size, sparkle_size), sparkle_size)
                screen.blit(sparkle_surface, (sparkle_x - sparkle_size, sparkle_y - sparkle_size))
        
        # Draw main essence (centered due to scaling)
        draw_x = self.rect.x - (self.image.get_width() - self.width) // 2
        draw_y = self.rect.y - (self.image.get_height() - self.height) // 2
        screen.blit(self.image, (draw_x, draw_y))

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=GRAY):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = pygame.Rect(x, y, width, height)
        
        # Create a solid gray platform instead of using texture
        # This will be much more visible against the space background
        self.image = pygame.Surface((width, height))
        self.image.fill(GRAY)
        
        # Add a white border to make it even more visible
        pygame.draw.rect(self.image, WHITE, (0, 0, width, height), 2)
        
        # Add some simple texture lines for visual interest
        for i in range(0, width, 20):
            pygame.draw.line(self.image, LIGHT_GRAY, (i, 0), (i, height), 1)
        for i in range(0, height, 10):
            pygame.draw.line(self.image, LIGHT_GRAY, (0, i), (width, i), 1)
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

class PuzzleBlock:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.activated = False
    
    def check_activation(self, player):
        # Simple puzzle: activate when player is standing on top of the block
        # Check if player is overlapping horizontally and standing on top
        player_bottom = player.y + player.height
        player_left = player.x
        player_right = player.x + player.width
        
        block_top = self.y
        block_left = self.x
        block_right = self.x + self.width
        
        # Check if player is on top of the block (within a small tolerance)
        on_top = (player_bottom >= block_top - 5 and player_bottom <= block_top + 10)
        
        # Check if player overlaps horizontally with the block
        horizontal_overlap = (player_right > block_left and player_left < block_right)
        
        if on_top and horizontal_overlap:
            self.activated = True
            print("Puzzle activated! Player is standing on the red block!")
        else:
            self.activated = False
    
    def draw(self, screen):
        color = YELLOW if self.activated else RED
        pygame.draw.rect(screen, color, self.rect)
        
        # Draw puzzle pattern
        pygame.draw.line(screen, BLACK, 
                        (self.x, self.y), 
                        (self.x + self.width, self.y + self.height), 3)
        pygame.draw.line(screen, BLACK, 
                        (self.x + self.width, self.y), 
                        (self.x, self.y + self.height), 3)
        
        # Add pulsing effect when not activated to make it more noticeable
        if not self.activated:
            import time
            pulse = int(abs(math.sin(time.time() * 3)) * 50)  # Pulsing brightness
            pulse_color = (255, pulse, pulse)  # Red with pulsing green/blue
            pygame.draw.rect(screen, pulse_color, self.rect, 3)
            
            # Add "PUZZLE" text above the block
            font = pygame.font.Font(None, 20)
            text = font.render("PUZZLE", True, BLACK)
            screen.blit(text, (self.x - 5, self.y - 25))

def load_background():
    """Load and scale background image"""
    try:
        # Try to load the space-themed background
        background = pygame.image.load("assets/pRSfmIss.jpeg").convert()
        background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        return background
    except pygame.error:
        print("Warning: Background image not found, using gradient background")
        # Create a gradient background as fallback
        background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            # Create a space-like gradient from dark blue to black
            color_value = int(50 * (1 - y / SCREEN_HEIGHT))
            color = (color_value, color_value, color_value + 20)
            pygame.draw.line(background, color, (0, y), (SCREEN_WIDTH, y))
        return background

def create_level_data(level_num):
    """Create level-specific data including platforms, enemies, and puzzle"""
    level_data = {
        'platforms': [],
        'bees': [],
        'dream_essences': [],  # Add dream essences
        'puzzle_pos': None,
        'player_start': (100, SCREEN_HEIGHT - 100),
        'background_color': WHITE,
        'level_name': f"Level {level_num}"
    }
    
    # Always add ground platform - make it more visible
    level_data['platforms'].append(Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, GRAY))
    
    if level_num == 1:
        # Level 1: Tutorial - Simple platforms, no enemies
        level_data['platforms'].extend([
            Platform(200, SCREEN_HEIGHT - 150, 150, 20),
            Platform(400, SCREEN_HEIGHT - 200, 120, 20),
        ])
        level_data['dream_essences'] = [(250, SCREEN_HEIGHT - 180), (150, SCREEN_HEIGHT - 80)]
        level_data['puzzle_pos'] = (450, SCREEN_HEIGHT - 220, 30, 20)
        level_data['level_name'] = "Level 1: Tutorial"
        
    elif level_num == 2:
        # Level 2: Introduction to enemies - 1 bee, more platforms
        level_data['platforms'].extend([
            Platform(150, SCREEN_HEIGHT - 120, 100, 20),
            Platform(300, SCREEN_HEIGHT - 180, 120, 20),
            Platform(500, SCREEN_HEIGHT - 140, 100, 20),
            Platform(650, SCREEN_HEIGHT - 220, 120, 20),
        ])
        level_data['bees'] = [(350, SCREEN_HEIGHT - 230)]
        level_data['dream_essences'] = [(180, SCREEN_HEIGHT - 150), (530, SCREEN_HEIGHT - 170)]
        level_data['puzzle_pos'] = (680, SCREEN_HEIGHT - 240, 30, 20)
        level_data['level_name'] = "Level 2: First Enemy"
        
    elif level_num == 3:
        # Level 3: Multiple enemies, vertical challenge
        level_data['platforms'].extend([
            Platform(100, SCREEN_HEIGHT - 120, 80, 20),
            Platform(250, SCREEN_HEIGHT - 200, 100, 20),
            Platform(450, SCREEN_HEIGHT - 160, 80, 20),
            Platform(600, SCREEN_HEIGHT - 280, 100, 20),
            Platform(300, SCREEN_HEIGHT - 320, 120, 20),
        ])
        level_data['bees'] = [
            (200, SCREEN_HEIGHT - 250),
            (500, SCREEN_HEIGHT - 210),
        ]
        level_data['dream_essences'] = [(130, SCREEN_HEIGHT - 150), (280, SCREEN_HEIGHT - 230), (630, SCREEN_HEIGHT - 310)]
        level_data['puzzle_pos'] = (350, SCREEN_HEIGHT - 340, 30, 20)
        level_data['level_name'] = "Level 3: Double Trouble"
        level_data['background_color'] = (240, 248, 255)  # Light blue
        
    elif level_num == 4:
        # Level 4: Maze-like with strategic bee placement
        level_data['platforms'].extend([
            Platform(120, SCREEN_HEIGHT - 100, 60, 20),
            Platform(220, SCREEN_HEIGHT - 160, 80, 20),
            Platform(350, SCREEN_HEIGHT - 120, 60, 20),
            Platform(450, SCREEN_HEIGHT - 200, 100, 20),
            Platform(580, SCREEN_HEIGHT - 140, 80, 20),
            Platform(200, SCREEN_HEIGHT - 280, 120, 20),
            Platform(400, SCREEN_HEIGHT - 320, 100, 20),
            Platform(600, SCREEN_HEIGHT - 260, 80, 20),
        ])
        level_data['bees'] = [
            (180, SCREEN_HEIGHT - 210),
            (380, SCREEN_HEIGHT - 250),
            (520, SCREEN_HEIGHT - 190),
        ]
        level_data['dream_essences'] = [(150, SCREEN_HEIGHT - 130), (380, SCREEN_HEIGHT - 150), (230, SCREEN_HEIGHT - 310), (610, SCREEN_HEIGHT - 290)]
        level_data['puzzle_pos'] = (430, SCREEN_HEIGHT - 340, 30, 20)
        level_data['level_name'] = "Level 4: The Gauntlet"
        level_data['background_color'] = (255, 248, 220)  # Light yellow
        
    elif level_num == 5:
        # Level 5: Final challenge - complex layout with strategic positioning
        level_data['platforms'].extend([
            Platform(80, SCREEN_HEIGHT - 100, 60, 20),
            Platform(180, SCREEN_HEIGHT - 140, 80, 20),
            Platform(300, SCREEN_HEIGHT - 100, 60, 20),
            Platform(400, SCREEN_HEIGHT - 180, 100, 20),
            Platform(540, SCREEN_HEIGHT - 120, 80, 20),
            Platform(660, SCREEN_HEIGHT - 200, 100, 20),
            Platform(150, SCREEN_HEIGHT - 240, 100, 20),
            Platform(320, SCREEN_HEIGHT - 280, 120, 20),
            Platform(500, SCREEN_HEIGHT - 320, 100, 20),
            Platform(250, SCREEN_HEIGHT - 380, 150, 20),
        ])
        level_data['bees'] = [
            (130, SCREEN_HEIGHT - 190),
            (350, SCREEN_HEIGHT - 230),
            (470, SCREEN_HEIGHT - 130),
            (600, SCREEN_HEIGHT - 250),
        ]
        level_data['dream_essences'] = [(110, SCREEN_HEIGHT - 130), (330, SCREEN_HEIGHT - 130), (570, SCREEN_HEIGHT - 150), (180, SCREEN_HEIGHT - 270), (530, SCREEN_HEIGHT - 350)]
        level_data['puzzle_pos'] = (300, SCREEN_HEIGHT - 400, 30, 20)
        level_data['level_name'] = "Level 5: Final Challenge"
        level_data['background_color'] = (255, 240, 245)  # Light pink
    
    return level_data

def create_game_objects(level_num=1):
    """Create and return all game objects for the specified level"""
    level_data = create_level_data(level_num)
    
    player = Player(*level_data['player_start'])
    
    # Create platforms from level data
    platforms = []
    for platform_data in level_data['platforms']:
        platforms.append(platform_data)
    
    # Create puzzle block
    puzzle_block = None
    if level_data['puzzle_pos']:
        puzzle_block = PuzzleBlock(*level_data['puzzle_pos'])
    
    # Create enemy groups
    hive_guard_bees = pygame.sprite.Group()
    stingers = pygame.sprite.Group()
    
    # Add bees from level data
    for bee_pos in level_data['bees']:
        hive_guard_bees.add(HiveGuardBee(*bee_pos))
    
    # Create dream essence group
    dream_essences = pygame.sprite.Group()
    
    # Add dream essences from level data
    for essence_pos in level_data['dream_essences']:
        dream_essences.add(DreamEssence(*essence_pos))
    
    return player, platforms, puzzle_block, hive_guard_bees, stingers, dream_essences, level_data

def main():
    # Set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Rüyalar ve Gerçeklik Arası - 2D Platformer")
    clock = pygame.time.Clock()
    
    # Load background
    background = load_background()
    
    # Game state
    current_level = 1
    level_complete_timer = 0
    game_complete = False
    game_over = False
    dream_essence_count = 0
    
    # Create game objects for first level
    player, platforms, puzzle_block, hive_guard_bees, stingers, dream_essences, level_data = create_game_objects(current_level)
    
    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Restart the current level
                    player, platforms, puzzle_block, hive_guard_bees, stingers, dream_essences, level_data = create_game_objects(current_level)
                    level_complete_timer = 0
                    game_over = False
                    dream_essence_count = 0
                    print(f"Level {current_level} restarted!")
                elif event.key == pygame.K_n and (game_complete or game_over):
                    # Start new game from level 1
                    current_level = 1
                    game_complete = False
                    game_over = False
                    level_complete_timer = 0
                    dream_essence_count = 0
                    player, platforms, puzzle_block, hive_guard_bees, stingers, dream_essences, level_data = create_game_objects(current_level)
                    print("New game started!")
        
        # Update game objects
        if player.health > 0 and not game_complete and not game_over:
            player.update(platforms + ([puzzle_block] if puzzle_block else []))
            if puzzle_block:
                puzzle_block.check_activation(player)
            
            # Update enemies
            for bee in hive_guard_bees:
                bee.update(player, stingers)
            
            # Update stingers
            stingers.update()
            
            # Update dream essences
            dream_essences.update()
            
            # Check collisions between stingers and player
            hit_stingers = pygame.sprite.spritecollide(player, stingers, True, 
                                                      collided=lambda p, s: p.rect.colliderect(s.rect))
            for stinger in hit_stingers:
                if player.take_damage(10):
                    game_over = True
                    print("GAME OVER! Player health reached zero!")
            
            # Check collisions between stingers and platforms
            for stinger in stingers:
                for platform in platforms:
                    if stinger.rect.colliderect(platform.rect):
                        stinger.kill()
                        break
            
            # Check collisions between player and dream essences
            collected_essences = pygame.sprite.spritecollide(player, dream_essences, True,
                                                           collided=lambda p, e: p.rect.colliderect(e.rect))
            for essence in collected_essences:
                dream_essence_count += 1
                print(f"Dream Essence collected! Total: {dream_essence_count}")
            
            # Check level completion
            if puzzle_block and puzzle_block.activated and level_complete_timer == 0:
                level_complete_timer = 1
                print(f"Level {current_level} completed!")
            
            # Handle level progression
            if level_complete_timer > 0:
                level_complete_timer += 1
                if level_complete_timer >= LEVEL_COMPLETE_DELAY:
                    if current_level < MAX_LEVELS:
                        current_level += 1
                        player, platforms, puzzle_block, hive_guard_bees, stingers, dream_essences, level_data = create_game_objects(current_level)
                        player.reset_health()  # Restore health for new level
                        level_complete_timer = 0
                        print(f"Welcome to Level {current_level}!")
                    else:
                        game_complete = True
                        print("Congratulations! You completed all levels!")
        
        # Draw everything
        # Draw background first
        screen.blit(background, (0, 0))
        
        # Draw platforms
        for platform in platforms:
            platform.draw(screen)
        
        # Draw puzzle block
        if puzzle_block:
            puzzle_block.draw(screen)
        
        # Draw dream essences
        for essence in dream_essences:
            essence.draw(screen)
        
        # Draw enemies
        for bee in hive_guard_bees:
            bee.draw(screen)
        
        # Draw stingers
        for stinger in stingers:
            stinger.draw(screen)
        
        # Draw player
        player.draw(screen)
        
        # Draw level information
        level_font = pygame.font.Font(None, 32)
        level_text = level_font.render(level_data['level_name'], True, BLACK)
        screen.blit(level_text, (SCREEN_WIDTH - 250, 10))
        
        # Draw progress
        progress_text = f"Level {current_level}/{MAX_LEVELS}"
        progress_surface = level_font.render(progress_text, True, BLACK)
        screen.blit(progress_surface, (SCREEN_WIDTH - 250, 45))
        
        # Draw instructions
        font = pygame.font.Font(None, 20)
        instructions = [
            "ARROW KEYS/WASD: Move and Jump",
            "Collect Dream Essences! Avoid bee stingers!",
            "Stand on RED BLOCK to complete level!",
            "R: Restart Level | ESC: Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, WHITE)
            # Add black outline for better visibility
            outline_text = font.render(instruction, True, BLACK)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                screen.blit(outline_text, (10 + dx, 10 + i * 22 + dy))
            screen.blit(text, (10, 10 + i * 22))
        
        # Show dream essence count
        essence_text = font.render(f"Dream Essences: {dream_essence_count}", True, CYAN)
        outline_essence = font.render(f"Dream Essences: {dream_essence_count}", True, BLACK)
        for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            screen.blit(outline_essence, (10 + dx, 100 + dy))
        screen.blit(essence_text, (10, 100))
        
        # Show puzzle status with clearer messaging
        if puzzle_block:
            if puzzle_block.activated:
                if level_complete_timer > 0:
                    puzzle_status = f"🎉 Level {current_level} Complete! Next level in {3 - level_complete_timer//60}..."
                else:
                    puzzle_status = "🎉 PUZZLE SOLVED! Great job! 🎉"
                status_color = GREEN
            else:
                puzzle_status = "❌ PUZZLE: Find and stand on the RED BLOCK!"
                status_color = RED
            
            status_text = font.render(puzzle_status, True, status_color)
            outline_status = font.render(puzzle_status, True, BLACK)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                screen.blit(outline_status, (10 + dx, 125 + dy))
            screen.blit(status_text, (10, 125))
        
        # Show player health
        health_text = font.render(f"Health: {player.health}/{player.max_health}", True, 
                                 GREEN if player.health > 50 else RED)
        outline_health = font.render(f"Health: {player.health}/{player.max_health}", True, BLACK)
        for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            screen.blit(outline_health, (10 + dx, 150 + dy))
        screen.blit(health_text, (10, 150))
        
        # Show game over if player is dead
        if game_over or player.health <= 0:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("GAME OVER!", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)
            
            # Show restart instruction
            restart_font = pygame.font.Font(None, 36)
            restart_text = restart_font.render("Press R to Restart Level | Press N for New Game", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            screen.blit(restart_text, restart_rect)
        
        # Show game complete screen
        elif game_complete:
            complete_font = pygame.font.Font(None, 64)
            complete_text = complete_font.render("CONGRATULATIONS!", True, GREEN)
            text_rect = complete_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(complete_text, text_rect)
            
            sub_font = pygame.font.Font(None, 36)
            sub_text = sub_font.render("You completed all levels!", True, BLACK)
            sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(sub_text, sub_rect)
            
            new_game_text = sub_font.render("Press N for New Game", True, BLUE)
            new_game_rect = new_game_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(new_game_text, new_game_rect)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
