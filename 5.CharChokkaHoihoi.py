from OpenGL.GL import *  
from OpenGL.GLU import *  
from OpenGL.GLUT import *  
import sys, time, math, random 

# --- Window ---
win_width, win_height = 1280, 720  #


# --- Ground ---
boundary_radius = 40.0  # Size of the cricket field
pitch_length = 20.0  
pitch_width = 3.0  
pitch_y = 0.5  # Height of the pitch above the ground
stumps_z = 10.0  # Position of the stumps, Upore or Niche from center
stumps_position_x = [-0.3, 0.0, 0.3]  # X-positions of the three stumps (left, middle, right)
stump_radius = 0.07  # Thickness of each stump
stump_height = 0.73  # Height of the stumps
bail = 0.03  # Size of the bails



# --- Ball ---
ball_radius = 0.11  # Size of the ball
ball_bounce_pitch = 0.45  # How much the ball bounces on the pitch (loses some speed)
ball_bounce_ground = 0.3  # How much the ball bounces on the ground (loses more speed as r dorkar nai ground mane it already got past the stumps)
ball_drag = 0.002  # Air resistance slowing the ball
g = -9.8  # Obhikorshoj Toron
ground_friction = 0.995  # Slows the ball when rolling on the ground
pitch_friction_x = 0.98  # Slows side-to-side movement on the pitch
pitch_friction_z = 0.995  # Slows forward-backward movement on the pitch



# --- Bat ---
bat_length = 1.05  
bat_side = 0.08  # Width/thickness of the bat
bat_handle = 0.26  
bat_pos = (0.0, 1.0, stumps_z + 0.5)  # Starting position near stumps
swing_speed = 82.0  # How fast the bat swings
bat_bounce = 1.2  # How much the ball bounces off the bat (makes it go farther)
swing_angle_max = 90.0  # Maximum angle the bat can swing
swing_time = 0.4  # How long a swing takes



# --- Shot Timing Meter ---
perfect_timing = 0.15  # Time window for a perfect hit
good_timing = 0.3  # Time window for a good hit
shot_power_max = 30.0  # Maximum power of a shot



# --- Game States ---
menu_state = 0  # Main menu screen
setup_state = 1  # Screen to choose batsman side (left or right-handed)
ready_state = 2  # Ready to bowl
bowling_state = 3  # Ball is being bowled
ball_flight_state = 4  # Ball is in the air
after_play_state = 5  # After a ball is played (hit or missed)
game_end_state = 6  # Game over screen
instructions_state = 7  # Instructions screen
state = menu_state  # Start the game in the main menu, initial state



# --- Game Info ---
camera_mode = 0  # Camera view (0 = TPS, 1 = FPS)
paused = False  # Whether the game is paused
runs = 0  # Players total score
wickets = 0  # Number of times batsman is out
balls_bowled = 0  # Number of balls bowled
total_balls = 15  # Total balls in the game
hud_msg = ""  # Message shown on screen (like "Wicket!" or "4 runs!")
pressed_keys = set()  # Tracks which keys are being pressed
last_time = None  # Tracks time for smooth updates
target_runs = random.randint(15, 35)  # Set random Target score to win
game_over = False  # Whether the game is over
last_state_change_time = None  # Time when the game state last changed



# ---Shot Feedback ---
shot_timing = ""  # Shows if hit was "Perfect", "Good", "Early", or "Late"
shot_power = 0.0  # Power of the shot (0.0 to 1.0) No shot-Maximum shot



# ---Batting Side Right or Left ---
batsman_right = 0  # Right-handed batsman
batsman_left = 1  # Left-handed batsman
batsman_side = batsman_right  # Default to right-handed
batsman_side_text = "Right"  # Text to show batsman side




# --- Menu Selection ---
menu_selection = 0  # Selected menu option (0 = Start, 1 = Instructions, 2 = Exit) 
menu_options = ["Start Game", "Instructions", "Exit"]  # Menu choices
setup_selection = 0  # Selected setup option (0 = Right-handed, 1 = Left-handed)



# --- Ball Clas to group all logic in one place---
class Ball:
    def __init__(self):
        self.reset()  # Set up the ball when the game starts
    
    def reset(self):
        # Balls initial position
        self.pos = [0.0, 2.5, -stumps_z - 5.0]  # (x, y, z) position
        speed = random.uniform(20.0, 30.0)  # Random speed for the ball
        self.vel = [random.uniform(-0.5, 0.5), random.uniform(0.0, 0.3), speed] # Sets random direction and speed for the ball (sideways, bounce/flight, speed towardds batsman)
        self.in_air = True  # Ball starts in the air
        self.first_ground_contact = None  # Tracks when ball first hits ground
        self.crossed_boundary_before_ground = False  # Checks if ball went out before landing
        self.launched = True  # Ball has been bowled
        self.scored = False  # Whether runs were scored
        self.wicket = False  # Whether ball hit stumps
        self.last_hit_msg = ""  # Message about the last hit
        self.has_hit_bat = False  # Whether ball hit the bat
        self.fly_mode = False  # Whether ball is in "flying" mode after a hit
        self.fly_start_time = 0  # Time when ball starts flying
        self.fly_duration = 2.0  # How long the ball flies
        self.start_pos = [0, 0, 0]  # Starting position after hit
        self.target_pos = [0, 0, 0]  # Target position after hit
        self.runs_added = 0  # Runs scored from the hit
        self.fly_bounces = 0  # Number of bounces after hit
        self.current_bounce = 0  # Current bounce number
        self.reach_batsman_time = None  # When ball should reach batsman
        self.actual_reach_time = None  # When ball actually reaches batsman

ball = Ball()  # Creates the ball object

# --- Bat Clas to group all logic in one place---
class Bat:
    def __init__(self):
        self.yaw = 0.0  # Horizontal rotation of bat
        self.pitch = 0.0  # Vertical rotation of bat
        self.swing_angle = 0.0  # Current swing angle
        self.swinging = False  # Whether bat is swinging
        self.swing_start_time = 0.0  # When swing started
        self.swing_direction = 0.0  # Direction of swing (-1 left, 1 right)

bat = Bat()  # Creates the bat object


# Position of the batsman (starts at origin, adjusted later)
batsman_pos = [0.0, 0.0, 0.0]

# ---------- Fielders ----------
# Positions of fielders (AI players who try to catch the ball)
fielders = [
    (20.0, 0.0, 25.0),  # Fielder 1 position (x, y, z)
    (-22.0, 0.0, 18.0),  # Fielder 2
    (28.0, 0.0, -5.0),   # Fielder 3
    (-25.0, 0.0, -15.0),  # Fielder 4
    (0.0, 0.0, 30.0),    # Fielder 5
    (10.0, 0.0, -28.0),  # Fielder 6
]


# Calculates the length of a vector , to calculate any target to target distance
def length(v): 
    result = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)  # Uses Pythagorean theorem ()x**2 + y**2 + z**2 )**0.5
    return result

# ---------- Rendering ----------
# Draws text on the screen (like scores or messages)
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)  # Sets position to start drawing text
    for char in text: 
        glutBitmapCharacter(font, ord(char))  # Draws each character



# Draws text centered at a position
def draw_text_centered(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    width = 0
    for char in text:
        width += glutBitmapWidth(font, ord(char))  # Calculates text width
    draw_text(x - width/2, y, text, font)  # Draws text centered



# Sets up the camera to view the game
def set_camera():
    glMatrixMode(GL_MODELVIEW)  # Sets up the view (like pointing a camera)
    glLoadIdentity()  # Resets the view
    if camera_mode == 0:  # TPS
        eye = (0.0, 13, -30.0)  # Camera position (x, y, z)
        center = (0.0, 1.0, stumps_z)  # Where camera looks
        up = (0, 1, 0)  # Up direction for camera
        gluLookAt(eye[0], eye[1], eye[2], center[0], center[1], center[2], up[0], up[1], up[2])
    else:  # FPS
        eye = [batsman_pos[0], 1.5, stumps_z - 1.5]  # Camera at batsman’s position
        center = [ball.pos[0], ball.pos[1], ball.pos[2]]  # Looks at the ball
        up = (0, 1, 0)  # Up direction
        gluLookAt(eye[0], eye[1], eye[2], center[0], center[1], center[2], up[0], up[1], up[2])



# Draws the ground (the field)
def draw_ground():
    glColor3f(0.1, 0.6, 0.1)  # Green grass
    R = boundary_radius + 5.0  # Makes ground slightly larger than boundary
    glBegin(GL_QUADS)  # Draws a square (quad) for the ground
    glVertex3f(-R, 0.0, -R)  # Bottom-left corner
    glVertex3f(R, 0.0, -R)   # Bottom-right
    glVertex3f(R, 0.0, R)    # Top-right
    glVertex3f(-R, 0.0, R)   # Top-left
    glEnd()



# Draws the boundary (edge of the field)
def draw_boundary():
    glColor3f(0.9, 0.6, 0.1)  # Orange-brown Line
    glLineWidth(4.0)  # Makes boundary line thick
    glBegin(GL_LINE_LOOP)  # Draws a circular line
    for i in range(64):  # Uses 64 points to make a smooth circle
        a = 2.0 * math.pi * i / 64.0  # Calculates angle for each point
        x = math.cos(a) * boundary_radius  # X-coordinate
        z = math.sin(a) * boundary_radius  # Z-coordinate
        glVertex3f(x, pitch_y + 0.01, z)  # Draws point slightly above ground
    glEnd()
    glLineWidth(1.0)  # Resets line thickness



# Draws the pitch and creases 
def draw_pitch_and_creases():
    px, pz = pitch_width, pitch_length  # Pitch dimensions
    glPushMatrix()  # Saves current position
    glTranslatef(0.0, pitch_y - 0.001, 0.0)  # Moves to pitch height
    glColor3f(0.6, 0.45, 0.25)  # Sets brown color for pitch
    glBegin(GL_QUADS)  # Draws pitch as a rectangle
    glVertex3f(-px/2, 0.0, -pz/2)  # Bottom-left
    glVertex3f(px/2, 0.0, -pz/2)   # Bottom-right
    glVertex3f(px/2, 0.0, pz/2)    # Top-right
    glVertex3f(-px/2, 0.0, pz/2)   # Top-left
    glEnd()
    glPopMatrix()  # Restores position
    for z in [stumps_z + 1.0, -stumps_z - 1.0]:  # Draws creases at both ends
        glColor3f(1, 1, 1)  # White color
        glLineWidth(3)  # Thick line
        glBegin(GL_LINES)  # Draws a line
        glVertex3f(-3.0, pitch_y + 0.001, z)  # Left end
        glVertex3f(3.0, pitch_y + 0.001, z)   # Right end
        glEnd()



# Draws the stumps and bails
def draw_stumps():
    glColor3f(0.55, 0.27, 0.07)  # Brown stumps
    for x in stumps_position_x:  # Draws each stump
        glPushMatrix()
        glTranslatef(x, pitch_y + stump_height/2.0, stumps_z)  # Moves to stump position
        glPushMatrix()
        glScalef(stump_radius * 2.0, stump_height, stump_radius * 2.0)  # Shapes stump
        glutSolidCube(1.0)  # Draws a cube for the stump
        glPopMatrix()
        glPopMatrix()
    if ball.wicket == False:  # Draws bails if stumps aren’t hit
        glColor3f(0.85, 0.7, 0.5)  # Light brown for bails
        for i in range(2):  # Draws two bails
            glPushMatrix()
            glTranslatef((i - 0.5) * 0.3, pitch_y + stump_height + bail, stumps_z)  # Positions bail
            glScalef(0.2, 0.04, 0.06)  # Shapes bail
            glutSolidCube(1.0)  # Draws bail
            glPopMatrix()



# Draws the ball
def draw_ball():
    glPushMatrix()
    glTranslatef(*ball.pos)  # Moves to ball’s position
    glColor3f(1.0, 0.2, 0.2)  # Red color for ball
    glutSolidSphere(ball_radius, 16, 12)  # Draws a sphere for the ball
    glPopMatrix()



# Draws the bat
def draw_bat():
    x, y, z = bat_pos  # Gets bat’s base position
    # Adjusts bat position based on batsman’s side
    if batsman_side == batsman_right:
        x += batsman_pos[0] + 0.35  # Moves bat right for right-handed batsman
    else:
        x += batsman_pos[0] - 0.35  # Moves bat left for left-handed
    z -= 1.5  # Positions bat in front of batsman
    glPushMatrix()
    glTranslatef(x, y, z)  # Moves to bat position
    glRotatef(90, 0, 1, 0)  # Rotates bat to face forward
    glRotatef(bat.yaw, 0, 1, 0)  # Applies horizontal swing
    glRotatef(bat.pitch, 1, 0, 0)  # Applies vertical swing
    glRotatef(bat.swing_angle, 0, 1, 0)  # Applies swing angle
    glPushMatrix()
    glTranslatef(0.0, 0.0, bat_length * 0.45)  # Centers bat
    if bat.swinging: 
        glColor3f(1.0, 0.9, 0.5)  # Yellowish when swinging
    else: 
        glColor3f(0.9, 0.75, 0.5)  # Brownish when still
    glScalef(bat_side * 1.2, 0.15, bat_length)  # Shapes bat
    glutSolidCube(1.0)  # Draws bat as a rectangular block
    glPopMatrix()
    glPopMatrix()



# Draws the batsman (a simple figure)
def draw_batsman():
    x, y, z = bat_pos
    x += batsman_pos[0]  # Adjusts for batsman’s position
    leg_set = 0.6  # Height of legs
    y = pitch_y + leg_set  # Places batsman on pitch
    glPushMatrix()
    glTranslatef(x, y, z - 1.5)  # Moves to batsman’s position
    glRotatef(90, 0, 1, 0)  # Rotates to face bowler
    glColor3f(0.9, 0.9, 0.9)  # White for body (like cricket uniform)
    glPushMatrix()
    glScalef(0.6, 1.2, 0.3)  # Shapes body
    glutSolidCube(1.0)  # Draws body
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 0.9, 0.0)  # Moves to head position
    glColor3f(1.0, 0.8, 0.6)  # Skin color for head
    glutSolidSphere(0.25, 16, 12)  # Draws head as a sphere
    glPopMatrix()
    glColor3f(0.2, 0.2, 0.8)  # Blue for legs (like cricket pads)
    for i in [-0.15, 0.15]:  # Draws two legs
        glPushMatrix()
        glTranslatef(i, -0.6, 0.0)  # Positions leg
        glScalef(0.2, 1.2, 0.2)  # Shapes leg
        glutSolidCube(1.0)  # Draws leg
        glPopMatrix()
    glPopMatrix()



# Draws the fielders
def draw_fielders():
    glColor3f(0.2, 0.8, 0.2)  # Green for fielders
    for f in fielders:
        glPushMatrix()
        glTranslatef(f[0], pitch_y, f[2])  # Moves to fielder’s position
        glScalef(0.5, 1.2, 0.5)  # Shapes fielder
        glutSolidCube(1.0)  # Draws fielder as a block
        glPopMatrix()



# Draws the main menu
def draw_menu():
    glClearColor(0.1, 0.1, 0.2, 1.0)  # Dark blue background
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clears screen
    glMatrixMode(GL_PROJECTION)  # Sets up 2D view for text
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, win_width, 0, win_height)  # Sets 2D coordinates
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 1.0, 0.2)  # Yellow for title
    draw_text_centered(win_width/2, win_height-100, "CHAR CHOKKA HOI HOI", GLUT_BITMAP_TIMES_ROMAN_24)
    for i, option in enumerate(menu_options):  # Draws menu options
        if i == menu_selection:
            glColor3f(1.0, 1.0, 0.0)  # Yellow for selected option
            draw_text_centered(win_width/2, win_height/2 - i*51, f"> {option} <")
        else:
            glColor3f(0.8, 0.8, 0.8)  # Gray for other options
            draw_text_centered(win_width/2, win_height/2 - i*51, option)
    glColor3f(0.7, 0.7, 0.7)  # Gray for instructions
    draw_text_centered(win_width/2, 100, "Use UP/DOWN arrows to select, ENTER to confirm")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()  # Shows the drawn frame



# Draws the setup screen (choose batsman side)
def draw_setup():
    glClearColor(0.1, 0.1, 0.2, 1.0)  # Dark blue background
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, win_width, 0, win_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 1.0, 0.2)  # Yellow for title
    draw_text_centered(win_width/2, win_height-100, "SELECT BATSMAN SIDE", GLUT_BITMAP_TIMES_ROMAN_24)
    options = ["Right-handed", "Left-handed"]  # Setup options
    for i, option in enumerate(options):
        if i == setup_selection:
            glColor3f(1.0, 1.0, 0.0)  # Yellow for selected
            draw_text_centered(win_width/2, win_height/2 - i*80, f"> {option} <")
        else:
            glColor3f(0.8, 0.8, 0.8)  # Gray for others
            draw_text_centered(win_width/2, win_height/2 - i*80, option)
    glColor3f(0.7, 0.7, 0.7)  # Gray for instructions
    draw_text_centered(win_width/2, 100, "Use UP/DOWN arrows to select, ENTER to confirm")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()



# Draws the instructions screen
def draw_instructions():
    glClearColor(0.1, 0.1, 0.2, 1.0)  # Dark blue background
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, win_width, 0, win_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 1.0, 0.2)  # Yellow for title
    draw_text_centered(win_width/2, win_height-80, "HOW TO PLAY", GLUT_BITMAP_TIMES_ROMAN_24)
    instructions = [  # List of instructions
        "1. Press 'B' to bowl the ball",
        "2. Use 'A' and 'D' keys to move batsman left/right",
        "3. Press SPACEBAR to swing the bat",
        "4. Time your swing perfectly for best results",
        "5. Score runs to reach the target",
        "6. Avoid getting all out ",
        "7. If 10 wickets down you lose ",
        "",
        "Press ESC to return to menu"
    ]
    glColor3f(0.9, 0.9, 0.9)  # White for text
    y_pos = win_height - 150
    for line in instructions:
        draw_text_centered(win_width/2, y_pos, line)
        y_pos -= 69  # Moves down for each line
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()





# --- Physics ---
def handle_bounce():
    x, y, z = ball.pos  # Gets balls position
    # Calculates half the pitch size for Pitch area
    px_half, pz_half = pitch_width / 2.0, pitch_length / 2.0  
    on_pitch = abs(x) <= px_half and abs(z) <= pz_half  # Checks if ball is on pitch

    if on_pitch:
        ground_level = pitch_y  # Pitch is raised, ball er bounce jate alada hoy, as amra alada korte parina ebhabe chara

    else:
        ground_level = 0.0  # Ground is at 0

    if y - ball_radius <= ground_level + 0.001:  # If ball hits ground
        ball.pos[1] = ground_level + ball_radius + 0.001  # Stops ball sinking, collision response


        if ball.vel[1] < 0:  # If ball is moving down (Sky to the ground, vy<0)

            if on_pitch:
                bounce = ball_bounce_pitch  # Bounce normally for pitch, Higher

            else:
                bounce = ball_bounce_ground  # Bounce factor for ground, lower
                
            ball.vel[1] = -ball.vel[1] * bounce  # as bounced so ekhon ulta dike jabe tai - and multiplying with bounce factor

            
            if on_pitch:            # After bouncing, the ball slows down
                ball.vel[0] *= pitch_friction_x  # Slows side-to-side
                ball.vel[2] *= pitch_friction_z  # Slows straight-back

            else:
                ball.vel[0] *= ground_friction
                ball.vel[2] *= ground_friction

        #6 calculation mainly
        if ball.first_ground_contact is None:       # Records first ground collision
            ball.first_ground_contact = (ball.pos[:], time.time())
            r2 = x**2 + z**2            #r**2 = x**2 + y**2, squared distance
            ball.crossed_boundary_before_ground = (r2 >= boundary_radius**2)




# Updates ball’s position based on its velocity
def integrate_ball(dt):
    if ball.in_air == False:  # If ball isn’t in air, don’t move
        return
    ball.vel[1] += g * dt  # Applies gravity to pull ball down v = gt, dt set in idle function
    for i in range(3):  # Updates position (x, y, z)
        ball.pos[i] += ball.vel[i] * dt         #Eulers Formula, new = old + vt



# Creates a new ball for the next delivery
def spawn_new_ball():
    ball.reset()  # Resets ball to starting position
    distance_to_batsman = stumps_z + 5.0  # Distance to batsman
    ball.reach_batsman_time = time.time() + distance_to_batsman / ball.vel[2]  # When ball reaches batsman    s = vt, t = s/v, to get the current system time when the ball is bowled.



# Starts a new ball delivery
def start_ball():
    global state, hud_msg, balls_bowled
    if state != ready_state or game_over:  # Only bowl if ready and game not over
        return
    balls_bowled += 1  # Counts the ball
    spawn_new_ball()  # Creates new ball
    state = ball_flight_state  # Changes to ball-in-air state
    hud_msg = "Bowling..."  # Shows message




# Resets the game for a new match and adding fielders
def reset():
    global runs, wickets, balls_bowled, state, hud_msg, target_runs, game_over, last_state_change_time, fielders
    runs =  0 
    wickets = 0
    balls_bowled = 0
    state = ready_state  # Sets to ready state
    target_runs = random.randint(18, 40)  # New random target score
    game_over = False  # Game not over
    last_state_change_time = None  # Clears last state change time
    spawn_new_ball()  # Creates new ball
    hud_msg = "New Over"  
    fielders.clear()  # Removes old fielders
    min_distance_from_pitch = pitch_length / 2 + 5.0  # Minimum distance of fielders from pitch
    min_distance_from_stumps = 5.0  # Minimum distance of fielders from stumps
    min_distance_between_fielders = 5.0  # Minimum distance between fielders
    num_of_fielders = 6
    for i in range(num_of_fielders):  # Places new fielders

        while True:
            theta = random.uniform(0, 2 * math.pi)  # Random angle in full circle
            radius = random.uniform(min_distance_from_pitch, boundary_radius - 2.0)  # Random radius from pitch to boundary
            x = math.cos(theta) * radius  # Calculates x = r * cos(theta)
            z = math.sin(theta) * radius  # Calculates z= r * sin(theta)
            distance_from_stumps = math.sqrt(x**2 + (z - stumps_z)**2)
            too_close = False

            for i in fielders:
                distance = math.sqrt((x - i[0])**2 + (z - i[2])**2)#Eucledian, destance calculation
                if distance < min_distance_between_fielders:
                    too_close = True
                    break
            outside_pitch = abs(x) > pitch_width / 2 + 1.0 or abs(z) > pitch_length / 2 + 1.0
            if distance_from_stumps >= min_distance_from_stumps and not too_close and outside_pitch:
                fielders.append((x, pitch_y, z))  # Adds fielder
                break




# Checks if the game is over
def check_game_over():
    global state, hud_msg, game_over
    if runs >= target_runs:  # If player scores enough runs
        state = game_end_state
        game_over = True
        hud_msg = "YOU WON!"
        return True
    
    elif wickets >= 10:  # If all wickets are lost
        state = game_end_state
        game_over = True
        hud_msg = "All Out! YOU LOST!"
        return True
    
    elif balls_bowled >= total_balls:  # If all balls are bowled
        state = game_end_state
        game_over = True
        if runs >= target_runs:
            hud_msg = "YOU WON!"
        else:
            hud_msg = "YOU LOST!"
        return True
    
    return False




# Checks if bat hits the ball and handles the result
def score_system():
    global runs, hud_msg, wickets, state, balls_bowled, last_state_change_time, shot_timing, shot_power
    if not bat.swinging: # If bat isn’t swinging, do nothing
        return  
    
    time_since_swing = time.time() - bat.swing_start_time

    if time_since_swing < swing_time:  # < 0.4
        swing_progress = time_since_swing / swing_time      #Normalizing to [0,1]
        swing_ease = math.sin(swing_progress * math.pi)  # Smooths swing motion, graph [0->peak->0]
        bat.swing_angle = swing_angle_max * swing_ease
    else:
        bat.swing_angle = 0.0  # Resets swing
        bat.swinging = False

    #Check if the ball is close enough to the batsman
    batsman_z = stumps_z - 1.5  # Batsman’s position
    distance_to_batsman = abs(ball.pos[2] - batsman_z)
    if distance_to_batsman < 1.0 and ball.has_hit_bat == False:  # If ball is close
        ball.has_hit_bat = True

        #Timing Evaluation
        current_time = time.time()
        if ball.reach_batsman_time:
            #How early or late the swing was.
            timing_diff = current_time - ball.reach_batsman_time
            # Determines timing quality
            if abs(timing_diff) <= perfect_timing:
                shot_timing = "Perfect!"
                timing_multiplier = 2.0
            elif abs(timing_diff) <= good_timing:
                shot_timing = "Good!"
                timing_multiplier = 1.2
            elif timing_diff < 0:
                shot_timing = "Early!"
                timing_multiplier = 0.5
            else:
                shot_timing = "Late!"
                timing_multiplier = 0.8
                
            shot_power = max(0.0, 1.0 - (abs(timing_diff) / good_timing)) #0,Fraction of timing error.


            if shot_timing == "Perfect!":
                base_runs = random.choice([4, 6])
            elif shot_timing == "Good!":
                base_runs = random.choice([2, 3, 4, 6])
            else:
                base_runs = random.choice([0, 1, 2])

            # Apply timing multiplier to base runs
            runs_added = max(0, round(base_runs * timing_multiplier))
            if runs_added >= 6:
                runs_added = 6
            if runs_added == 5:
                runs_added = random.choice([4, 6])
            else:
                runs_added = runs_added


            runs += runs_added  # Adds runs
            ball.runs_added = runs_added
            ball.scored = True
            ball.in_air = False
            state = after_play_state
            last_state_change_time = time.time()
            ball.fly_mode = True  # Ball flies after hit
            ball.fly_start_time = time.time()
            ball.start_pos = ball.pos[:]  # Saves start position

            #Ball spider, scoring angle
            if random.random() < 0.50:
                angle = random.uniform(-math.pi/2, math.pi/2)  # Off-side
            else:
                angle = random.uniform(math.pi/2, 3*math.pi/2)  # Leg-side



            # Sets distance based on runs, kotodur gelo r koybar bounce khailo
            if runs_added == 0:
                distance = 5.0
                ball.fly_bounces = 1


            elif runs_added <= 2:
                distance = 10.0 + shot_power * 10.0
                ball.fly_bounces = random.choice([1, 2])


            elif runs_added <= 3:
                distance = 15.0 + shot_power * 15.0
                ball.fly_bounces = random.choice([1, 2])

            elif runs_added == 4:
                distance = boundary_radius + 2.0
                ball.fly_bounces = random.choice([1, 2, 3])

            else:
                distance = boundary_radius + 5.0
                ball.fly_bounces = 0

            #ball er flight kothay giye thambe, Defines where the ball lands after hit. polar to cartesian
            ball.target_pos = [ 
                ball.pos[0] + math.cos(angle) * distance, #x = rcos(angle)
                ball.pos[1],
                ball.pos[2] + math.sin(angle) * distance  #y = sin(angle)
            ]


            ball.fly_duration = 1.0 + (distance / boundary_radius) * 2.0
            ball.current_bounce = 0
            # Shows hit result
            if runs_added == 0:
                hud_msg = f"{shot_timing} Dot ball"
            # else:
            #     hud_msg = f"{shot_timing} {runs_added} run{'s' if runs_added > 1 else ''}!"
            
            else:
                if runs_added == 1:
                    run_label = "run"
                else:
                    run_label = "runs"
                
                # Combine shot timing, run count, and run label
                hud_msg = f"{shot_timing} {runs_added} {run_label}!"

            if check_game_over():
                return




# Checks if ball hits stumps (wicket)
def bowled_out():
    global wickets, hud_msg, state, balls_bowled, last_state_change_time

    if ball.wicket == True or ball.in_air == False:
        return
    x, y, z = ball.pos

    if abs(z - stumps_z) < 1.0 and y <= stump_height + 0.5:  # If ball is near stumps
        for i in stumps_position_x:
            if abs(x - i) <= (stump_radius + ball_radius + 0.1):    #(distance between balls x to current stamps(left, middle, right) <= )
                ball.wicket = True
                wickets += 1  # Adds a wicket
                hud_msg = "WICKET!"
                state = after_play_state
                last_state_change_time = time.time()
                ball.scored = True
                ball.in_air = False
                check_game_over()
                return




# Checks if a fielder catches the ball
def caught_out():
    global wickets, hud_msg, state, balls_bowled, last_state_change_time
    if ball.wicket == True or ball.fly_mode == False:
        return
    
    if ball.runs_added not in [2, 3, 4]:  # Only check for certain shots
        return
    
    for f in fielders:
        fx, fy, fz = f
        dx = ball.pos[0] - fx
        dz = ball.pos[2] - fz
        distance = math.sqrt(dx*dx + dz*dz)
        if distance < 2.0:  # If ball is near fielder
            catch_chance = 0.4  # Base chance of catch
            if shot_timing == "Early!" or shot_timing == "Late!":
                catch_chance = 0.6
            elif shot_timing == "Good!":
                catch_chance = 0.3
            elif shot_timing == "Perfect!":
                catch_chance = 0.1
            if random.random() < catch_chance:
                ball.wicket = True
                wickets += 1
                hud_msg = "Caught Out!"
                state = after_play_state
                last_state_change_time = time.time()
                ball.fly_mode = False
                ball.scored = True
                ball.in_air = False
                check_game_over()
                return



# Updates the game state
def update(dt):
    global batsman_pos, state, balls_bowled, game_over, last_state_change_time, shot_timing, shot_power, menu_selection, setup_selection

    if state in [menu_state, setup_state, instructions_state, game_end_state]:
        return  # Don’t update in these states
    
    if game_over: 
        return
    
    move_speed = 8.0  # How fast batsman moves
    if 'd' in pressed_keys or 'D' in pressed_keys: 
        batsman_pos[0] -= move_speed * dt  # Moves left
        bat.swing_direction = max(-1.0, bat.swing_direction - dt * 2.0)
    if 'a' in pressed_keys or 'A' in pressed_keys: 
        batsman_pos[0] += move_speed * dt  # Moves right
        bat.swing_direction = min(1.0, bat.swing_direction + dt * 2.0)
    if 'd' not in pressed_keys and 'D' not in pressed_keys and 'a' not in pressed_keys and 'A' not in pressed_keys:
        if bat.swing_direction > 0:
            bat.swing_direction = max(0.0, bat.swing_direction - dt * 2.0)
        else:
            bat.swing_direction = min(0.0, bat.swing_direction + dt * 2.0)
    batsman_pos[0] = max(-pitch_width/2 + 0.3, min(pitch_width/2 - 0.3, batsman_pos[0]))  # Keeps batsman on pitch
    if ball.in_air and not ball.fly_mode:
        if state == ball_flight_state:
            integrate_ball(dt)  # Moves ball
            handle_bounce()  # Checks for bounce
            score_system()  # Checks for bat hit
            bowled_out()  # Checks for stump hit
            if ball.actual_reach_time is None and ball.pos[2] >= stumps_z - 1.5:
                ball.actual_reach_time = time.time()
            if ball.pos[2] > stumps_z + 5:  # If ball passes batsman
                state = after_play_state
                last_state_change_time = time.time()
                hud_msg = "Dot Ball"
                ball.in_air = False
                check_game_over()
    if ball.fly_mode:  # If ball is flying after hit
        t = (time.time() - ball.fly_start_time) / ball.fly_duration
        t = min(t, 1.0)  # Limits to 1
        ball.pos[0] = ball.start_pos[0] + (ball.target_pos[0] - ball.start_pos[0]) * t  # Moves x
        ball.pos[2] = ball.start_pos[2] + (ball.target_pos[2] - ball.start_pos[2]) * t  # Moves z
        if ball.fly_bounces > 0:  # If ball bounces
            segment = 1.0 / (ball.fly_bounces + 1)
            local_t = (t % segment) / segment
            max_height = 2.0 + shot_power * 4.0
            ball.pos[1] = ball.start_pos[1] + math.sin(local_t * math.pi) * max_height
            if t >= (ball.current_bounce + 1) * segment:
                ball.current_bounce += 1
        else:
            max_height = 3.0 + shot_power * 5.0
            ball.pos[1] = ball.start_pos[1] + max_height * math.sin(t * math.pi)
        caught_out()  # Checks for catch
        if t >= 1.0:  # If flight ends
            ball.fly_mode = False
            if state != after_play_state:
                state = ready_state
                spawn_new_ball()
                hud_msg = ""
                check_game_over()
    if state == after_play_state:  # After ball is played
        if last_state_change_time is not None:
            time_since_change = time.time() - last_state_change_time
            if time_since_change > 2.0:  # Waits 2 seconds
                state = ready_state
                spawn_new_ball()
                hud_msg = ""
                ball.scored = False
                ball.wicket = False
                ball.has_hit_bat = False
                shot_timing = ""
                shot_power = 0.0
                check_game_over()

# Draws the game
def display():
    if state == menu_state:
        draw_menu()  # Shows menu
        return
    elif state == setup_state:
        draw_setup()  # Shows setup screen
        return
    elif state == instructions_state:
        draw_instructions()  # Shows instructions
        return
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clears screen
    set_camera()  # Sets camera
    draw_ground()  # Draws field
    draw_boundary()  # Draws boundary
    draw_pitch_and_creases()  # Draws pitch
    draw_stumps()  # Draws stumps
    draw_batsman()  # Draws batsman
    draw_bat()  # Draws bat
    draw_ball()  # Draws ball
    draw_fielders()  # Draws fielders
    glMatrixMode(GL_PROJECTION)  # Sets 2D for text
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, win_width, 0, win_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 1.0, 1.0)  # White for text
    draw_text(10, win_height-20, f"Runs: {runs}/{target_runs}  Wickets: {wickets}  Ball: {balls_bowled}/{total_balls}")
    draw_text(10, win_height-50, f"Batsman: {batsman_side_text}-handed")
    if shot_timing:  # Shows timing feedback
        if shot_timing == "Perfect!":
            glColor3f(0.2, 1.0, 0.2)  # Green
        elif shot_timing == "Good!":
            glColor3f(0.2, 0.8, 1.0)  # Blue
        else:
            glColor3f(1.0, 0.5, 0.2)  # Orange
        draw_text_centered(win_width/2, win_height/2, shot_timing, GLUT_BITMAP_TIMES_ROMAN_24)
    glColor3f(1.0, 1.0, 1.0)  # White for message
    draw_text(10, win_height-80, f"Msg: {hud_msg}")
    if bat.swinging:  # Shows shot power meter
        glColor3f(0.3, 0.3, 0.3)  # Gray background
        glBegin(GL_QUADS)
        glVertex2f(win_width/2 - 102, win_height - 100)
        glVertex2f(win_width/2 + 102, win_height - 100)
        glVertex2f(win_width/2 + 102, win_height - 80)
        glVertex2f(win_width/2 - 102, win_height - 80)
        glEnd()
        if shot_timing == "Perfect!":
            glColor3f(0.2, 1.0, 0.2)
        elif shot_timing == "Good!":
            glColor3f(0.2, 0.8, 1.0)
        elif shot_timing:
            glColor3f(1.0, 0.5, 0.2)
        else:
            glColor3f(1.0, 1.0, 0.0)  # Yellow
        meter_width = 200 * shot_power
        glBegin(GL_QUADS)  # Draws power meter
        glVertex2f(win_width/2 - 100, win_height - 98)
        glVertex2f(win_width/2 - 100 + meter_width, win_height - 98)
        glVertex2f(win_width/2 - 100 + meter_width, win_height - 82)
        glVertex2f(win_width/2 - 100, win_height - 82)
        glEnd()
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)  # Draws meter outline
        glVertex2f(win_width/2 - 100, win_height - 100)
        glVertex2f(win_width/2 + 100, win_height - 100)
        glVertex2f(win_width/2 + 100, win_height - 80)
        glVertex2f(win_width/2 - 100, win_height - 80)
        glEnd()
        glLineWidth(1.0)
        draw_text_centered(win_width/2, win_height - 120, "SHOT POWER")
    if game_over:  # Shows game over screen
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_QUADS)
        glColor4f(0.0, 0.0, 0.0, 0.5)  # Semi-transparent overlay
        glVertex2f(0, 0)
        glVertex2f(win_width, 0)
        glVertex2f(win_width, win_height)
        glVertex2f(0, win_height)
        glEnd()
        glDisable(GL_BLEND)
        glColor3f(1.0, 1.0, 1.0)
        text = "YOU WON!" if runs >= target_runs else "YOU LOST!"
        draw_text_centered(win_width/2, win_height/2, text, GLUT_BITMAP_HELVETICA_18)
        draw_text_centered(win_width/2, win_height/2 - 40, "Press R to play again or ESC for menu")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()

# Handles keyboard presses
def keyboard(key, x, y):
    global pressed_keys, state, camera_mode, menu_selection, setup_selection, batsman_side, batsman_side_text
    pressed_keys.add(key.decode('utf-8'))  # Tracks pressed key
    if state == menu_state:
        if key == b'\r':  # Enter key
            if menu_selection == 0:  # Start Game
                state = setup_state
                setup_selection = 0
            elif menu_selection == 1:  # Instructions
                state = instructions_state
            elif menu_selection == 2:  # Exit
                sys.exit(0)
        elif key == b'\x1b':  # ESC
            sys.exit(0)
        return
    elif state == setup_state:
        if key == b'\r':  # Enter key
            if setup_selection == 0:  # Right-handed
                batsman_side = batsman_right
                batsman_side_text = "Right"
                batsman_pos[0] = -1.0
            else:  # Left-handed
                batsman_side = batsman_left
                batsman_side_text = "Left"
                batsman_pos[0] = 1.0
            reset()
            state = ready_state
        elif key == b'\x1b':  # ESC
            state = menu_state
        return
    elif state == instructions_state:
        if key == b'\x1b':  # ESC
            state = menu_state
        return
    if game_over:
        if key == b'r': 
            reset()  # Restarts game
        elif key == b'\x1b': 
            state = menu_state
        return
    if key == b' ' and state == ball_flight_state:
        if not bat.swinging:
            bat.swinging = True
            bat.swing_start_time = time.time()  # Starts swing
    elif key == b'r': 
        reset()
    elif key == b'b': 
        start_ball()  # Bowls ball
    elif key == b'c': 
        camera_mode = (camera_mode + 1) % 2  # Switches camera
    elif key == b'\x1b': 
        state = menu_state

# Handles key releases
def keyboard_up(key, x, y):
    pressed_keys.discard(key.decode('utf-8'))  # Stops tracking key

# Handles special keys (like arrow keys)
def special_keys(key, x, y):
    global menu_selection, setup_selection
    if state == menu_state:
        if key == GLUT_KEY_UP:
            menu_selection = (menu_selection - 1) % len(menu_options)  # Moves up
        elif key == GLUT_KEY_DOWN:
            menu_selection = (menu_selection + 1) % len(menu_options)  # Moves down
    elif state == setup_state:
        if key == GLUT_KEY_UP:
            setup_selection = (setup_selection - 1) % 2
        elif key == GLUT_KEY_DOWN:
            setup_selection = (setup_selection + 1) % 2

# Adjusts the window when resized
def reshape(w, h):
    glViewport(0, 0, w, h)  # Sets drawing area
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, w/float(h), 0.1, 100.0)  # Sets 3D perspective
    glMatrixMode(GL_MODELVIEW)

# Updates game regularly
def idle():
    global last_time
    t = time.time()
    if last_time:
        dt = t - last_time
    else:
        dt = 0.016  # assume ~60 FPS default step
 # Time since last update
    last_time = t
    update(dt)  # Updates game state
    glutPostRedisplay()  # Redraws screen

# Main function to start the game
def main():
    global last_time
    glutInit(sys.argv)  # Starts OpenGL
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Sets display mode
    glutInitWindowSize(win_width, win_height)  # Sets window size
    glutCreateWindow(b"Cricket Challenge")  # Creates window
    glEnable(GL_DEPTH_TEST)  # Enables 3D depth
    glClearColor(0.5, 0.7, 1.0, 1.0)  # Light blue background
    glutDisplayFunc(display)  # Sets display function
    glutReshapeFunc(reshape)  # Sets resize function
    glutKeyboardFunc(keyboard)  # Sets keyboard function
    glutKeyboardUpFunc(keyboard_up)  # Sets key release function
    glutSpecialFunc(special_keys)  # Sets special key function
    glutIdleFunc(idle)  # Sets update function
    last_time = time.time()
    glutMainLoop()  # Starts the game loop

if __name__ == "__main__":
    main()  # Runs the game