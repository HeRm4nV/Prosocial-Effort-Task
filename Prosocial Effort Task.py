#!/usr/bin/env python3.10.9
# coding=utf-8

"""
tested in Python 3.10.9
"""
import pygame, sys, os, cv2
from pygame.locals import FULLSCREEN, USEREVENT, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_c
from os.path import join
from time import gmtime, strftime
from pylsl import StreamInfo, StreamOutlet
from math import ceil, sqrt
import itertools
from random import shuffle

debug_mode = True

class TextRectException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message

# Configurations:
FullScreenShow = True  # Pantalla completa automáticamente al iniciar el experimento
keys = [pygame.K_SPACE]  # Teclas elegidas para mano derecha o izquierda
test_name = "PET"
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
effort_levels = [20, 30, 40, 60, 70, 80]
credits_levels = [2, 3, 4, 5, 6, 7]

# triggers:
start_trigger = 500
stop_trigger = 550
slide_trigger = 100
decision_start_trigger = 200
decision_made_trigger = 210
not_decision_made_trigger = 250
start_task_trigger = 300
last_button_pressed_trigger = 260
correct_task_trigger = 350
failed_task_trigger = 360
resting_trigger = 400

# block_type = division, total
block_type = "division"

min_buttons = 10

practice_iterations = 1
decision_practice_trials = 4

# Asegurar que el número de bloques sea relativo al número de combinaciones posibles
# ex: (con 50 combinaciones no se pueden hacer 3 bloques, porque 50/3 = 16.6)
# combinaciones actuales 6*6 = 36 (6 niveles de esfuerzo, 6 niveles de créditos)
blocks_number = 3
max_answer_time = 10 # Tiempo máximo para responder en segundos
max_decision_time = 6 # Tiempo máximo para decidir en segundos

optimal_square = [1, 2, 3, 4, 6, 8, 9, 12, 15, 16, 18, 20, 21, 24, 25, 27, 28, 30, 32, 35, 36, 40, 42, 45, 48, 49, 50]

# buttons configuration
base_button_color = (255, 255, 255)
pressed_button_color = (0, 255, 0)

# Onscreen instructions
def select_slide(slide_name):

    if slide_name.startswith("intro_block"):
        slide_to_use = "intro_block"
    else:
        slide_to_use = slide_name

    basic_slides = {
        'welcome': [
            u"Bienvenido/a, a este experimento!!!",
            " ",
            u"Se te indicará paso a paso que hacer."
        ],
        'intro_block': [
            u"Ahora comenzará el " + ("primer" if len(slide_name.split("_")) == 3 and slide_name.split("_")[2] == "1" else "segundo" if len(slide_name.split("_")) == 3 and slide_name.split(
                "_")[2] == "2" else "tercer") + " bloque del experimento",
            " ",
            u"Puedes descansar unos segundos, cuando te sientas",
            u"listo para comenzar presiona Espacio para continuar."
        ],
        'Instructions_Casillas': [
            u"Tarea de las Casillas:",
            " ",
            u"Abajo puedes encontrar un esquema de la tarea",
            u"Tu meta es hacer click en el mayor número de casillas en 10 segundos. Esta tarea será mostrada 2 veces"
        ],
        'Interlude_Casillas': [
            u"¡Muy bien! Ahora INTENTA Y SUPERA TU RENDIMIENTO!"
        ],
        'Exit_Casillas': [
            u"Gracias por completar la tarea.",
            " ",
            u"Procede ahora a la siguiente pagina para las instrucciones de la próxima tarea."
        ],
        'Instructions_Decision_1': [
            u"Tarea de decisiones:",
            " ",
            u"En esta tarea, tú podrás hacer click en cierto número de casillas para ganar créditos que serán convertidos en dinero.",
            u"Estos créditos pueden ser otorgados a ti, o a otro/a participante de esta investigación",
            u"quien estará completando otro tipo de pruebas.",
            " ",
            u"Se te ha asignado el rol de Jugador 1, mientras que a otro/a participante se le ha asignado el rol de Jugador 2.",
            u"Esto significa que tomarás decisiones que afectarán al Jugador 2, pero él no tomará decisiones que te afecten a ti.",
            " ",
            u"En cada ronda de esta tarea, tendrás que elegir entre dos opciones:",
            " ",
            u'"Descansar": No tendrás que hacer click en ninguna casilla y podrás descansar a cambio de 1 crédito.',
            u'"Trabajar": Tendrás que hacer click en las casillas para ganar una mayor cantidad de créditos',
            " ",
            u"En algunas rondas (rondas TI), decidirás si quieres ganar créditos para ti mismo.",
            u"En otras rondas (rondas OTRO), decidirás si quieres ganar créditos para otro/a jugador/a anónimo/a.",
            u"Los créditos que ganes serán convertidos en dinero.",
            u"En rondas TI, tú recibirás este dinero. En las rondas OTRO, el dinero será recibido por otro jugador.",
            " ",
            u"Tus decisiones serán completamente anónimas y confidenciales."
        ],
        'Instructions_Decision_2': [
            u"A continuación puedes ver 2 casos de ejemplo,", 
            u"el primero es para un caso de decisión para TI y el segundo para OTRO"
        ],
        'Instructions_Decision_3': [
            u"Cada ronda mostrará 1 crédito por Descansar, y {} o {} créditos".format((', '.join(str(x) for x in credits_levels[:-1])), credits_levels[-1]),
            u"por hacer click a un determinado número de casillas.",
            " ",
            u"Tienes un máximo de {} segundos para responder.".format(max_decision_time), 
            u"Si tardas más de {} segundos, se darán 0 créditos a ti o a la otra persona dependiendo de la ronda.".format(max_decision_time),
            " ",
            u"Si eliges hacer click en las casillas para ganar más créditos,", 
            u"debes hacer click en todas las casillas en la pantalla en 10 segundos.",
            u"De lo contrario, no se otorgarán créditos para esa ronda.",
            " ",
            u"Siempre que elijas Descansar, podrás hacerlo durante 10 segundos y no tendrás que hacer click en ninguna casilla."
        ],
        'Instructions_Decision_final': [
            u"Recuerda, en cada ronda:",
            " ",
            u"• Verás si los créditos serán para TI beneficio o para al de un/a OTRO/A desconocido/a.",
            " ",
            u"• Debes escoger entre dos opciones: Una opción te da 1 crédito por descansar, la otra", 
            u"te da más créditos pero debes hacer click en un número de casillas.",
            " ",
            u"• Tendrás {} segundos para tomar una decisión, de lo contrario se darán 0 créditos para esa ronda.".format(max_decision_time),
            " ",
            u"Continúa con la página siguiente para una ronda de práctica. Aquí verás cómo se hace click en las casillas.", 
            u"Tu objetivo es hacer click en el número de casillas que se muestran en la pantalla.", 
            u"Ya que es sólo práctica, no se obtendrás créditos en estas rondas."
        ],
        'Effort_ending': [
            u"¡Genial! ya has practicado cómo hacer click en las casillas", 
            u"para así ganar créditos para TI o para a él/la OTRO/A participante.",
            " ",
            u"Ahora tendrás una ronda de práctica que es similar a la tarea que tendrás que realizar en este estudio.",
            u"Como fue dicho anteriormente, aquí podrás elegir entre Descansar y ganar 1 crédito,",
            u"o hacer click en las casillas para ganar una mayor cantidad de créditos. "
        ],
        'Practice_ending': [
            u"¡Excelente! Has completado la ronda de práctica.",
            " ",
            u"Ahora comenzarás con la tarea principal.",
            " ",
            u"Recuerda que en cada ronda tendrás que tomar una decisión entre Descansar y Trabajar.",
            u"Si eliges Trabajar, tendrás que hacer click en todas las casillas en la pantalla en 10 segundos.",
            u"Si eliges Descansar, podrás hacerlo durante 10 segundos y no tendrás que hacer click en ninguna casilla."
        ],
        'TestingDecision': [
            u"Recordar que si no se toma ninguna decisión",
            u"No ganarás créditos"
        ],
        'Break': [
            u"Puedes tomar un descanso.",
            " ",
            u"Cuando te sientas listo para continuar presiona Espacio."
        ],
        'wait': [
            "+"
        ],
        'farewell': [
            u"El experimento ha terminado.",
            "",
            u"Muchas gracias por su colaboración!!"
        ]
    }

    selected_slide = basic_slides[slide_to_use]

    return (selected_slide)

#%% Stream LSL
# Function to initialize the LSL stream
def init_lsl():
    if debug_mode:
        return
    
    """Creates an LSL outlet"""
    global outlet
    info = StreamInfo(name="TriggerStream", type="Markers", channel_count=1,
                      channel_format="double64", source_id="Stream")
    outlet = StreamOutlet(info)
    print('LSL stream created')

# Function to send triggers using LSL
def send_trigger(trigger):
    if debug_mode:
        return
    
    """Sends a trigger to the LSL outlet"""
    try:
        outlet.push_sample([trigger])
        print('Trigger ' + str(trigger) + ' sent')
    except:
        print('Failed to send trigger ' + str(trigger))


# Text and screen Functions
def setfonts():
    """Sets font parameters"""
    global bigchar, char, charnext
    pygame.font.init()
    font = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar = pygame.font.Font(font, 96)
    char = pygame.font.Font(font, 32)
    charnext = pygame.font.Font(font, 24)


def render_textrect(string, font, rect, text_color, background_color, justification=1):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 left-justified
                    1 (default) horizontally centered
                    2 right-justified

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    import pygame

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException(
                        "The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)

    # Let's try to write the text out on the surface.
    surface = pygame.Surface(rect.size)
    surface.fill(background_color)

    accumulated_height = 0
    for line in final_lines:
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise TextRectException(
                "Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(
                    tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width -
                             tempsurface.get_width(), accumulated_height))
            else:
                raise TextRectException(
                    "Invalid justification argument: " + str(justification))
        accumulated_height += font.size(line)[1]

    return final_lines, surface


def paragraph(text, key=None, no_foot=False, color=None):
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color

    for line in text:
        phrase = char.render(line, True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40
    if key != None:
        if key == K_SPACE:
            foot = u"Para continuar presione la tecla ESPACIO..."
        elif key == K_RETURN:
            foot = u"Para continuar presione la tecla ENTER..."
    else:
        foot = u"Responda con la fila superior de teclas de numéricas"
    if no_foot:
        foot = ""

    nextpage = charnext.render(foot, True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()


def slide(text, info, key, limit_time=0):
    """Organizes a paragraph into a slide"""
    paragraph(text, key, info)
    wait_time = wait(key, limit_time)
    return wait_time


def calibration_slide(text, key, image=None):    
    screen.fill(background)
    row = screen.get_rect().height // 8

    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40

    if image != None:
        picture = pygame.image.load("media\\images\\" + image)
        picture = pygame.transform.scale(picture, (screen.get_rect().height/2*picture.get_width()/picture.get_height(), screen.get_rect().height/2))        
        rect = picture.get_rect()
        rect = rect.move((screen.get_rect().width/2 - picture.get_width()/2,row + 40))
        screen.blit(picture, rect)
    


    nextpage = charnext.render(u"Para continuar presione la tecla ESPACIO...", True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()
    wait_time = wait(key, 0)
    return wait_time


def cases_slide(text, key, images=[]):    
    screen.fill(background)
    row = screen.get_rect().height // 8
    first_image = 0

    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40

    for image in images:
        picture = pygame.image.load("media\\images\\" + image)
        picture = pygame.transform.scale(picture, (screen.get_rect().width/2, screen.get_rect().width/2*picture.get_height()/picture.get_width()))        
        rect = picture.get_rect()
        rect = rect.move(( (1+(2*first_image)) * screen.get_rect().width/4 - picture.get_width()/2, row + 40))
        screen.blit(picture, rect)
        first_image += 1

    nextpage = charnext.render(u"Para continuar presione la tecla ESPACIO...", True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()
    wait_time = wait(key, 0)
    return wait_time


def blackscreen(blacktime=0):
    """Erases the screen"""
    screen.fill(background)
    pygame.display.flip()
    pygame.time.delay(blacktime)


def wait(key, limit_time):
    """Hold a bit"""

    TIME_OUT_WAIT = USEREVENT + 1
    if limit_time != 0:
        pygame.time.set_timer(TIME_OUT_WAIT, limit_time, loops=1)

    tw = pygame.time.get_ticks()

    switch = True
    while switch:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            elif event.type == KEYUP:
                if event.key == key:
                    switch = False
            elif event.type == TIME_OUT_WAIT and limit_time != 0:
                switch = False

    pygame.time.set_timer(TIME_OUT_WAIT, 0)
    pygame.event.clear()                    # CLEAR EVENTS

    return (pygame.time.get_ticks() - tw)


def ends():
    """Closes the show"""
    blackscreen()
    dot = char.render('.', True, char_color)
    dotbox = dot.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(dot, dotbox)
    pygame.display.flip()
    while True:
        for evento in pygame.event.get():
            if evento.type == KEYUP and evento.key == K_ESCAPE:
                pygame_exit()


def windows(text, key=None, limit_time=0): 
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 120

    font = pygame.font.Font(None, 90)

    if "TI" in text[1] or "OTRO" in text[1]:
        phrase = font.render(text[0], True, (0, 0, 0))
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 120

        font = pygame.font.Font(None, 140)

        color = (255, 0, 0) if text[1] == "TI" else (0, 0, 255)

        phrase = font.render(text[1], True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
    
    else:
        for line in text:
            phrase = font.render(line, True, (0, 128, 0))
            phrasebox = phrase.get_rect(centerx=center[0], top=row)
            screen.blit(phrase, phrasebox)
            row += 120

    pygame.display.flip()
    wait(key, limit_time)


# Program Functions
def init():
    """Init display and others"""
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color, fix, fixbox, fix_think, fixbox_think, izq, der, quest, questbox
    pygame.init()  # soluciona el error de inicializacion de pygame.time
    pygame.display.init()
    pygame.display.set_caption(test_name)
    pygame.mouse.set_visible(False)
    if FullScreenShow:
        resolution = (pygame.display.Info().current_w,
                      pygame.display.Info().current_h)
        screen = pygame.display.set_mode(resolution, FULLSCREEN)
    else:
        try:
            resolution = pygame.display.list_modes()[3]
        except:
            resolution = (1280, 720)
        screen = pygame.display.set_mode(resolution)
    center = (int(resolution[0] / 2), int(resolution[1] / 2))
    izq = (int(resolution[0] / 8), (int(resolution[1] / 8)*7))
    der = ((int(resolution[0] / 8)*7), (int(resolution[1] / 8)*7))
    background = Color('lightgray')
    char_color = Color('black')
    charnext_color = Color('black')
    fix = char.render('+', True, char_color)
    fixbox = fix.get_rect(centerx=center[0], centery=center[1])
    fix_think = bigchar.render('+', True, Color('red'))
    fixbox_think = fix.get_rect(centerx=center[0], centery=center[1])
    quest = bigchar.render('?', True, char_color)
    questbox = quest.get_rect(centerx=center[0], centery=center[1])
    screen.fill(background)
    pygame.display.flip()


def pygame_exit():
    pygame.quit()
    sys.exit()


def optimal_division(n):
    if n not in optimal_square:
        n = next(x[0] for x in enumerate(optimal_square) if x[1] > n)
        n = optimal_square[n]

    factors = [(i, n // i) for i in range(1, int(sqrt(n)) + 1) if n % i == 0]
    a, b = min(factors, key=lambda x: abs(x[0] - x[1]))
    return min(a, b)#, min(a, b)


def draw_buttons(buttons_count, rows, hborder, vborder):
    # how many columns we need?
    columns = ceil(buttons_count / rows)

    button_list = []

    for i in range(1, buttons_count + 1):
        # create buttons with the i number below the title in 5 rows and all inside the screen
        button = pygame.Rect((((resolution[0]/columns) * ((i-1)//rows) + hborder), (((resolution[1])/(rows + 1)) * ((i-1)%rows + 1) + vborder)), (resolution[0]/columns - (hborder*2), resolution[1]/(rows + 1) - (vborder*2)))
        pygame.draw.rect(screen, base_button_color, button, 0, 45)
        font = pygame.font.Font(None, 36)
        text = font.render(str(i), True, (0, 0, 0))
        text_rect = text.get_rect(center=button.center)
        screen.blit(text, text_rect)
        button_list.append(button)

    pygame.display.flip()
    return button_list


def show_buttons(buttons_count, rows = 5, hborder = 10, vborder = 20, max_time = 10, title_text = ""):    
    stage_change = USEREVENT + 2
    pygame.time.set_timer(stage_change, max_time * 1000)

    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    screen.fill(background)
    pygame.display.flip()

    buttons_pressed = []
    done = False
    
    # Draw a title text at the top of the screen
    font = pygame.font.Font(None, 36)
    
    if "TI" in title_text:
        text = font.render(title_text, True, (255, 0, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))

        text2 = font.render(title_text[:-2], True, (0, 128, 0))
        
        text_width, text_height = text2.get_size()
        top_left = text_rect.topleft
        pygame.draw.rect(screen, (background), (top_left[0], top_left[1], text_width, text_height))

        text_rect2 = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))
    
    
    elif "OTRO" in title_text:
        text = font.render(title_text, True, (0, 0, 255))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))
        
        text2 = font.render(title_text[:-4], True, (0, 128, 0))

        text_width, text_height = text2.get_size()
        top_left = text_rect.topleft
        pygame.draw.rect(screen, (background), (top_left[0], top_left[1], text_width, text_height))

        text_rect2 = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))

    else:
        text = font.render(title_text, True, (0, 128, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))

    screen.blit(text, text_rect)
    if "OTRO" in title_text or "TI" in title_text:
        screen.blit(text2, text_rect2)

    buttons = draw_buttons(buttons_count, rows, hborder, vborder)
    # first image of a block, is identify by +100
    #send_trigger(new_image_trigger + (10 if image_list[count].split(directory_separator)[-1][:-4] in animals_id_list else 0) + (50 if image_list[count].split(directory_separator)[-2].endswith("pos") else 0) + 100)

    timer_text = pygame.font.Font(None, 36)
    text = timer_text.render(str(max_time) + " s", True, (0, 0, 0))
    seconds_text_rect = text.get_rect(center=(resolution[0] * 0.9, resolution[1]/((rows+1)*2)))
    screen.blit(text, seconds_text_rect)
    pygame.display.flip()

    # Show mouse
    pygame.mouse.set_visible(True)

    first_button_pressed_time = None
    last_button_pressed_time = None

    tw = pygame.time.get_ticks()
    rt = 0

    send_trigger(start_task_trigger)
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_c:
                done=True

            # Show time left on top right corner of the screen
            elif event.type == seconds:
                # Erased the previous text in that space
                pygame.draw.rect(screen, background, seconds_text_rect, 0)

                # Draw the new time left
                rt = pygame.time.get_ticks() - tw
                text = timer_text.render(str(max_time - int(rt/1000)) + " s", True, (0, 0, 0))
                screen.blit(text, seconds_text_rect)
                pygame.display.flip()

            # Detect if user press one button with the mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.collidepoint(event.pos):
                        #print(f"Button {i+1} pressed")
                        # Change button color and without border
                        pygame.draw.rect(screen, pressed_button_color, button, 0, 45)
                        font = pygame.font.Font(None, 36)
                        text = font.render(str(i+1), True, (0, 0, 0))
                        button_text_rect = text.get_rect(center=button.center)
                        screen.blit(text, button_text_rect)
                        pygame.display.flip()

                        # save the button pressed
                        if i+1 not in buttons_pressed:
                            if first_button_pressed_time == None:
                                first_button_pressed_time = pygame.time.get_ticks() - tw
                            buttons_pressed.append(i+1)
                            if len(buttons_pressed) == buttons_count:
                                send_trigger(last_button_pressed_trigger)
                                last_button_pressed_time = pygame.time.get_ticks() - tw

            elif event.type == stage_change:
                #print ("Cambiando de bloque")
                done = True

    pygame.time.set_timer(stage_change, 0)
    pygame.mouse.set_visible(False)
    pygame.event.clear()               # CLEAR EVENTS

    # Return the buttons pressed count
    return len(buttons_pressed), len(buttons_pressed) == buttons_count, first_button_pressed_time, last_button_pressed_time


def take_decision(buttons_number, credits_number, title_text, max_time = 6, test = False):
    screen.fill(background)

    font = pygame.font.Font(None, 72)

    if "TI" in title_text:
        offset = 2
        offset_color = (255, 0, 0)

    elif "OTRO" in title_text:
        offset = 4
        offset_color = (0, 0, 255)

    text = font.render(title_text[:-offset], True, (0, 128, 0))
    text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
    text2 = font.render(title_text[-offset:], True, offset_color)
    text_rect2 = text2.get_rect(center=(resolution[0]/2, (resolution[1]/6) + 100))

    screen.blit(text, text_rect)
    screen.blit(text2, text_rect2)

    '''
    # horizontal buttons
    button_positions = [1, 5]

    shuffle(button_positions)

    # we gonna create 2 buttons, one for credits/effort and the other for resting
    button1 = pygame.Rect((resolution[0]/8*button_positions[0], resolution[1]/8*4), (resolution[0]/4, resolution[1]/4))
    button2 = pygame.Rect((resolution[0]/8*button_positions[1], resolution[1]/8*4), (resolution[0]/4, resolution[1]/4))
    '''

    button_positions = [4, 8]

    shuffle(button_positions)
    # we gonna create 2 buttons, one for credits/effort and the other for resting
    button1 = pygame.Rect((resolution[0]/8*3, resolution[1]/12*button_positions[0]), (resolution[0]/4, resolution[1]/4))
    button2 = pygame.Rect((resolution[0]/8*3, resolution[1]/12*button_positions[1]), (resolution[0]/4, resolution[1]/4))

    pygame.draw.rect(screen, base_button_color, button1, 0, 45)
    pygame.draw.rect(screen, base_button_color, button2, 0, 45)

    font = pygame.font.Font(None, 36)
    text = font.render(f"{credits_number} créditos", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button1.center[0], centery=button1.center[1] - 20)
    screen.blit(text, text_rect)
    text = font.render(f"por {buttons_number} cajas", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button1.center[0], centery=button1.center[1] + 20)
    screen.blit(text, text_rect)

    text = font.render("1 crédito", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button2.center[0], centery=button2.center[1] - 20)
    screen.blit(text, text_rect)
    text = font.render("por descansar", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button2.center[0], centery=button2.center[1] + 20)
    screen.blit(text, text_rect)

    # button border
    pygame.draw.rect(screen, (0, 0, 0), button1, 1, 45)
    pygame.draw.rect(screen, (0, 0, 0), button2, 1, 45)

    # mouse_image
    if test:
        picture = pygame.image.load("media\\images\\" + "mouse_scroll_wheel.png").convert_alpha()
        picture = pygame.transform.scale(picture, (screen.get_rect().height/8*picture.get_width()/picture.get_height(), screen.get_rect().height/8))

        row = center[1] - screen.get_rect().height/16 + picture.get_height()
        rect = picture.get_rect()
        rect = rect.move((screen.get_rect().width/10*8 - picture.get_width()/2, row))
        screen.blit(picture, rect)

        # text up the mouse image
        font = pygame.font.Font(None, 36)
        text = font.render("Gira la rueda del ratón hacia arriba", True, (0, 0, 0))
        text_rect = text.get_rect(center=(screen.get_rect().width/10*8, row - 40))
        screen.blit(text, text_rect)

        # text down the mouse image
        text = font.render("Gira la rueda del ratón hacia abajo", True, (0, 0, 0))
        text_rect = text.get_rect(center=(screen.get_rect().width/10*8, row + 40 + picture.get_height()))
        screen.blit(text, text_rect)

    pygame.display.flip()

    done = False

    selected_button = 0
    scroll_type = None

    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    tw = pygame.time.get_ticks()
    rt = 0

    # Show mouse
    #pygame.mouse.set_visible(True)

    reaction_time = None

    send_trigger(decision_start_trigger)
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                    pygame_exit()
            
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    reaction_time = pygame.time.get_ticks() - tw
                    scroll_type = "up"
                    if button_positions[0] == 4:
                        selected_button = 1
                    else:
                        selected_button = 2
                elif event.y < 0:
                    reaction_time = pygame.time.get_ticks() - tw
                    scroll_type = "down"
                    if button_positions[0] == 4:
                        selected_button = 2
                    else:
                        selected_button = 1
                done = True

            elif event.type == seconds:
                # Draw the new time left
                rt = pygame.time.get_ticks() - tw
                if rt >= max_time * 1000:
                    pygame.time.set_timer(seconds, 0)
                    done = True
                
            '''
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button1.collidepoint(event.pos):
                    #print(f"Button 1 pressed")
                    # Change button color and without border
                    pygame.draw.rect(screen, pressed_button_color, button1, 0, 45)
                    pygame.display.flip()
                    done = True
                    selected_button = 1

                elif button2.collidepoint(event.pos):
                    #print(f"Button 2 pressed")
                    # Change button color and without border
                    pygame.draw.rect(screen, pressed_button_color, button2, 0, 45)
                    pygame.display.flip()
                    done = True
                    selected_button = 2
            '''

    #pygame.mouse.set_visible(False)

    return (selected_button, scroll_type, reaction_time)


def show_resting(title_text, max_time = 10):

    screen.fill(background)
    font = pygame.font.Font(None, 42)

    if "TI" in title_text:
        text = font.render(title_text, True, (255, 0, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
        text2 = font.render(title_text[:-2], True, (0, 128, 0))

    elif "OTRO" in title_text:
        text = font.render(title_text, True, (0, 0, 255))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
        text2 = font.render(title_text[:-4], True, (0, 128, 0))

    text_width, text_height = text2.get_size()
    top_left = text_rect.topleft
    pygame.draw.rect(screen, (background), (top_left[0], top_left[1], text_width, text_height))
    text_rect2 = text.get_rect(center=(resolution[0]/2, resolution[1]/10))

    screen.blit(text, text_rect)
    screen.blit(text2, text_rect2)

    timer_text = pygame.font.Font(None, 42)
    text = timer_text.render(str(max_time) + " s", True, (0, 0, 0))
    seconds_text_rect = text.get_rect(center=(resolution[0] * 0.9, resolution[1]/10))
    screen.blit(text, seconds_text_rect)

    resting_text = pygame.font.Font(None, 90)
    text = resting_text.render("DESCANSO", True, (0, 0, 0))
    resting_text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/2))
    screen.blit(text, resting_text_rect)

    pygame.display.flip()

    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    tw = pygame.time.get_ticks()
    rt = 0

    while True:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
            elif event.type == seconds:
                # Erased the previous text in that space
                pygame.draw.rect(screen, background, seconds_text_rect, 0)

                # Draw the new time left
                rt = pygame.time.get_ticks() - tw
                text = timer_text.render(str(max_time - int(rt/1000)) + " s", True, (0, 0, 0))
                screen.blit(text, seconds_text_rect)
                pygame.display.flip()

                if rt >= max_time * 1000:
                    pygame.time.set_timer(seconds, 0)
                    return


def task(self_combinations, other_combinations, blocks_number, block_type, max_answer_time, 
         test = False, decision_practice_trials = 1, file = None, effort_table = None):

    last_list_cut = 0
    actual_list_cut = len(self_combinations)//blocks_number

    for _ in range(blocks_number):
        if block_type == "division":
            actual_combinations_list = self_combinations[last_list_cut:actual_list_cut] + other_combinations[last_list_cut:actual_list_cut]
        elif block_type == "total":
            actual_combinations_list = self_combinations + other_combinations
        else:
            print("Tipo de bloque no reconocido")
            break

        shuffle(actual_combinations_list)

        practice_count = 0

        for combination in actual_combinations_list:
            # Clear buttons time
            first_button_pressed_time, last_button_pressed_time = None, None

            # Intro
            windows([f"Créditos para", combination[2]], K_SPACE, 2000)

            # Selection
            selection, scroll_type, decision_reaction_time = take_decision(combination[0], combination[1], f"Créditos para {combination[2]}", max_time = max_decision_time, test = test)

            if selection not in [1, 2]:
                if test:
                    while selection not in [1, 2]:
                        slide(select_slide('TestingDecision'), False, K_SPACE)
                        # if return is 1, the participant selected a credit button, else a resting button
                        selection, scroll_type, decision_reaction_time = take_decision(combination[0], combination[1], f"Créditos para {combination[2]}", max_time = max_decision_time, test =  test)
                else:        
                    show_resting(f"Créditos para {combination[2]}", max_time = 10)

            button_clear = False

            # Trial
            if selection == 1:
                buttons_pressed, button_clear, first_button_pressed_time, last_button_pressed_time = show_buttons(buttons_count = combination[0], rows = optimal_division(combination[0]), hborder = 10, vborder = 20, max_time = max_answer_time, title_text = f"Créditos para {combination[2]}")
                earned_credits = combination[1]
                if not button_clear:
                    earned_credits = 0
                    show_resting(f"Créditos para {combination[2]}", max_time = 10)
                    send_trigger(failed_task_trigger)
                else:
                    send_trigger(correct_task_trigger)

            elif selection == 2:
                show_resting(f"Créditos para {combination[2]}", max_time = 10)
                earned_credits = 1
                send_trigger(resting_trigger)

            else:
                print("No se ha seleccionado decisiones")
                earned_credits = 0
                send_trigger(not_decision_made_trigger)
            
            # Earned credits
            if not test:
                #("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("NivelEsfuerzo", "NivelReward", "Condición", "Decisión", "CuadrosClickeados", "ÉxitoTarea", "CréditosGanados", "TiempoReacciónDecisión", "TiempoReacciónPrimerCuadro", "TiempoReacciónÚltimoCuadro"))
                if file != None:
                    file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (effort_table[combination[0]], combination[1], "Self" if combination[2] == "TI" else "Other", "task" if selection == 1 else ("resting" if selection == 2 else "no decision"), buttons_pressed, "True" if selection == 2 else button_clear, earned_credits, decision_reaction_time, first_button_pressed_time, last_button_pressed_time))
                    file.flush()
                if combination[2] == "TI":
                    windows(["Has ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
                else:
                    windows(["Otra persona ha ganado", f"{earned_credits} créditos"], K_SPACE, 1000)

            if test:
                practice_count += 1
                if practice_count >= decision_practice_trials:
                    break

        if not test:
            slide(select_slide('Break'), False, K_SPACE)
            last_list_cut = actual_list_cut
            actual_list_cut += len(self_combinations)//blocks_number
        else:
            slide(select_slide('Practice_ending'), False, K_SPACE)
            return

# Main Function
def main():
    """Game's main loop"""

    init_lsl()

    # Si no existe la carpeta data se crea
    if not os.path.exists('data/'):
        os.makedirs('data/')

    # Username = id_condition_geometry_hand
    subj_name = input(
        "Ingrese el ID del participante y presione ENTER para iniciar: ")

    while (len(subj_name) < 1):
        os.system('cls')
        print("ID ingresado no cumple con las condiciones, contacte con el encargado...")
        subj_name = input(
            "Ingrese el ID del participante y presione ENTER para iniciar: ")

    pygame.init()

    csv_name = join('data', date_name + "_" + subj_name + ".csv")
    dfile = open(csv_name, 'w')
    # condition = self/other
    dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("NivelEsfuerzo", "NivelReward", "Condición", "Decisión", "CuadrosClickeados", "ÉxitoTarea", "CréditosGanados", "TiempoReacciónDecisión", "TiempoReacciónPrimerCuadro", "TiempoReacciónÚltimoCuadro"))
    dfile.flush()

    init()

    send_trigger(start_trigger)

    #selection, scroll_type = take_decision(13, 2, f"Créditos para OTRO", max_time = 6)

    #cases_slide(select_slide('Instructions_Decision_2'), K_SPACE, ["TI_schema.png", "OTRO_schema.png"])

    #print(f"Selection: {selection}, Scroll: {scroll_type}")

    slide(select_slide('welcome'), False, K_SPACE)

    # ------------------- calibration block ------------------------
    send_trigger(slide_trigger + 10)
    calibration_slide(select_slide('Instructions_Casillas'), K_SPACE, "testing_schema.jpg")

    max_button_count, _, _, _ = show_buttons(buttons_count = 50, rows = optimal_division(50), hborder = 10, vborder = 20, max_time = max_answer_time, title_text = "Comienza!")

    send_trigger(slide_trigger + 20)
    slide(select_slide('Interlude_Casillas'), False, K_SPACE)

    actual_button_count, _, _, _ = show_buttons(buttons_count = 50, rows = 5, hborder = 10, vborder = 20, max_time = max_answer_time, title_text = "Comienza!")

    if actual_button_count > max_button_count:
        max_button_count = actual_button_count

    if max_button_count < min_buttons:
        max_button_count = min_buttons
    

    # ------------------- Decision instructions block ------------------------
    send_trigger(slide_trigger + 30)
    slide(select_slide('Instructions_Decision_1'), False, K_SPACE)
    send_trigger(slide_trigger + 40)
    cases_slide(select_slide('Instructions_Decision_2'), K_SPACE, ["TI_schema.jpg", "OTRO_schema.jpg"])
    send_trigger(slide_trigger + 50)
    slide(select_slide('Instructions_Decision_3'), False, K_SPACE)
    send_trigger(slide_trigger + 60)
    slide(select_slide('Instructions_Decision_final'), False, K_SPACE)

    # ------------------------ Training Section -----------------------------
    effort_levels_recalculated = [ceil(max_button_count*(effort/100)) for effort in effort_levels]
    # effort table effort_levels_recalculated: effort_levels
    effort_table = dict(zip(effort_levels_recalculated, effort_levels))

    self_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, ["TI"]*len(effort_levels_recalculated)))
    other_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, ["OTRO"]*len(effort_levels_recalculated)))

    shuffle(self_combinations)
    shuffle(other_combinations)

    # Testing Trials for all effort levels
    for _ in range(practice_iterations):
        for effort_level in effort_levels_recalculated:
            show_buttons(buttons_count = effort_level, rows = optimal_division(effort_level), hborder = 10, vborder = 20, max_time = max_answer_time, title_text = f"Créditos para TI")

    # Testing full block
    send_trigger(slide_trigger + 70)        
    slide(select_slide('Effort_ending'), False, K_SPACE)

    task(self_combinations, other_combinations, blocks_number, block_type, max_answer_time, test = True, decision_practice_trials = 1)

    # ------------------------ Experiment Section -----------------------------
    # Experiment Starting
    task(self_combinations, other_combinations, blocks_number, block_type, max_answer_time, file = dfile, effort_table = effort_table)

    dfile.flush()

    send_trigger(slide_trigger + 80)
    slide(select_slide('farewell'), True, K_SPACE)
    send_trigger(stop_trigger)
    dfile.close()
    ends()


# Experiment starts here...
if __name__ == "__main__":
    main()
