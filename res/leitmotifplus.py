#leitmotif+ graphic shnyaga
#он же лейтмотиф-2, лейтмотиф дважды
#почему? потому что я хочу единую херь написанную чуть лучше

import pygame as pg

class Window():
    def __init__(self, rect, font, line_height, objects):
        self.rect = rect
        self.font = font
        self.line_height = line_height
        self.objects = {}
        self.raw_objects = objects
        self.active_textbox = None

        self.recalculate()

    def recalculate(self):
        rect = self.rect
        line_height = self.line_height

        x,y,w,h = rect
        w-=8
        h-=8
        
        self.max_lines = int(h/line_height)
        max_lines = self.max_lines
        self.indent = (h-max_lines*line_height)/2
        indent = self.indent

        self.states = {}

        for object_name in self.raw_objects:
            if self.raw_objects[object_name]["type"] in ["item_list","item_sel"]:
                self.states[object_name] = ["",0]
            elif self.raw_objects[object_name]["type"] in ["imagebox_selection"]:
                self.states[object_name] = [False,None]
            elif self.raw_objects[object_name]["type"] in ["textbox"]:
                self.states[object_name] = ""
            else:
                self.states[object_name] = False
            self.objects[object_name] = self.raw_objects[object_name]
            obj_rect = []
            for dim in self.objects[object_name]["rect"]:
                if type(dim) == str: 
                    obj_rect.append(eval(dim))
                    #АХТУНГ! eval() - очень, ОЧЕНЬ плохо. но парсер я писать не буду. хоть убейте.
                else:
                    obj_rect.append(dim)
            self.objects[object_name]["rect"] = obj_rect

    def update(self,target,m_state, unicode):
        draw_convex(target, self.rect)

        for obj_name in self.objects:
            obj = self.objects[obj_name]
            if obj["active"]:
                obj_rect = (obj["rect"][0]+self.rect[0]+4, obj["rect"][1]+self.rect[1]+4, obj["rect"][2], obj["rect"][3])

                if obj["type"] == "convex": #выпуклость
                    draw_convex(target, obj_rect)
                elif obj["type"] == "indent": #углубление
                    draw_indent(target, obj_rect)
                elif obj["type"] == "label": #текст
                    draw_aligned_line(target, obj_rect, obj["align"], obj["text"], self.font)
                elif obj["type"] == "button": #кнопка
                    self.states[obj_name] = draw_button(target, obj_rect, obj["align"], obj["text"], self.font, m_state)
                elif obj["type"] == "multitext": #многострочный текст
                    draw_multitext(target, obj_rect, obj["items"], self.font, self.line_height)
                elif obj["type"] == "item_list": #список для выбора (state[0] - выбор, state[1] - прокрут)
                    self.states[obj_name] = draw_itemlist(target, obj_rect, obj["items"], self.states[obj_name][0], self.states[obj_name][1], self.font, self.line_height, m_state)
                elif obj["type"] == "item_sel": #картиночки для выбора (state[0] - выбор, state[1] - прокрут)
                    self.states[obj_name] = draw_itemsel(target, obj_rect, obj["items"], self.states[obj_name][0], self.states[obj_name][1], self.line_height*2-2, m_state)
                elif obj["type"] == "textbox": #поле для ввода
                    self.states[obj_name], is_active = draw_textbox(target, obj_rect, self.states[obj_name], self.font, self.active_textbox == obj_name, unicode, m_state)
                    if is_active: self.active_textbox = obj_name
                    elif not is_active and self.active_textbox == obj_name: self.active_textbox = ""
                elif obj["type"] == "imagebox":
                    self.states[obj_name] = draw_imagebox(target, obj_rect, obj["img"], obj["scale"], obj["offset"] if "offset" in obj else (0,0), m_state)
                elif obj["type"] == "imagebox_selection":
                    self.states[obj_name] = draw_imagebox(target, obj_rect, obj["img"], obj["scale"], obj["offset"], m_state, obj["selection"])
            else:
                if self.objects[obj_name]["type"] in ["button"]: self.states[obj_name] = False

    def get_state(self, source_obj):
        if source_obj in self.objects:
            if self.objects[source_obj]["type"] in ["item_list","item_sel"]:
                return self.states[source_obj][0]
            else:
                return self.states[source_obj]
        else:
            return None
            

def draw_convex(target,rect, base_color = (196,196,196), light_color = (230,230,230), dark_color = (108,108,108)):
    shade = 2
    x,y,w,h = rect
    pg.draw.rect(target,base_color,(x,y,w,h))
    pg.draw.polygon(target, light_color, ((x, y), (x+w, y), (x+w-shade, y+shade), (x+shade, y+h-shade), (x, y+h)))
    pg.draw.polygon(target, dark_color, ((x+w-shade, y+shade), (x+w, y), (x+w, y+h), (x, y+h), (x+shade, y+h-shade)))
    pg.draw.rect(target, base_color, (x+shade, y+shade, w-shade*2, h-shade*2))


def draw_indent(target,rect, base_color = (196,196,196), light_color = (108,108,108), dark_color = (230,230,230)):
    shade = 2
    x,y,w,h = rect
    pg.draw.rect(target,base_color,(x,y,w,h))
    pg.draw.polygon(target, light_color, ((x, y), (x+w, y), (x+w-shade, y+shade), (x+shade, y+h-shade), (x, y+h)))
    pg.draw.polygon(target, dark_color, ((x+w-shade, y+shade), (x+w, y), (x+w, y+h), (x, y+h), (x+shade, y+h-shade)))
    pg.draw.rect(target, base_color, (x+shade, y+shade, w-shade*2, h-shade*2))

def draw_aligned_line(target,rect,aligment,text,font,color=(16,16,16)):
    x,y,w,h = rect
    x,y,w,h = x+2,y,w-4,h

    line_rect = pg.Surface((w,h),pg.SRCALPHA)
    #line_rect.convert()
    line = font.render(str(text),True,color)
    lw, lh = line.get_size()

    if aligment == "left":line_rect.blit(line,(0,(h-lh)/2))
    elif aligment == "right":line_rect.blit(line,(w-lw,(h-lh)/2))
    elif aligment == "textbox":
        if lw <= w:line_rect.blit(line,(0,(h-lh)/2))
        else: line_rect.blit(line,(w-lw,(h-lh)/2))
    else:line_rect.blit(line,((w-lw)/2,(h-lh)/2))
     
    target.blit(line_rect,(x,y))

def draw_button(target, rect, aligment, text, font, m_state):
    x,y,w,h = rect

    clicked = False

    if x <= m_state[0] <= x+w and y <= m_state[1] <= y+h and m_state[3]:
        clicked = True

    if clicked:
        draw_indent(target, (x+2,y+2,w-4,h-4))
    else:
        draw_convex(target, (x+2,y+2,w-4,h-4))

    draw_aligned_line(target,(x+2,y,w-4,h),aligment,text,font)

    return clicked*m_state[2]
    
def draw_multitext(target, rect, lines, font, line_height):
    x,y,w,h = rect
    x,y,w,h = x+2,y,w-4,h
    
    max_lines = int(h/line_height)
    top_ind = (h-max_lines*line_height)/2

    draw_items = lines[-max_lines:] + [""]*(max_lines-len(lines[-max_lines:]))

    draw_indent(target,(x,y,w,h))
    for ind, line in enumerate(draw_items):
        draw_aligned_line(target,(x+2,y+top_ind+ind*line_height,w-4,line_height),"left",line,font)


def draw_itemlist(target, rect, items, selection, scroll, font, line_height, m_state):
    light_color = (230,230,230)
    dark_color = (108,108,108)

    x,y,w,h = rect
    x,y,w,h = x+2,y,w-4,h

    scrollbar_width, margin = 18,12
    max_lines = int(h/line_height)
    top_ind = (h-max_lines*line_height)/2

    draw_items = items[scroll:scroll+max_lines] + [""]*(max_lines-len(items[scroll:scroll+max_lines]))

    draw_indent(target,(x,y,w-scrollbar_width-margin,h))
    for ind, line in enumerate(draw_items):
        if x+2 <= m_state[0] <= x+w-scrollbar_width-margin-2 and y+top_ind+ind*line_height <= m_state[1] <= y+top_ind+(ind+1)*line_height and m_state[2] and line != "":
            if selection == line: selection = ""
            else:selection = line

        if selection == line and line != "":
            pg.draw.rect(target,(16,16,16),(x+2,y+top_ind+ind*line_height,w-scrollbar_width-margin-4,line_height))
            draw_aligned_line(target,(x+2,y+top_ind+ind*line_height,w-scrollbar_width-margin-4,line_height),"left",line,font,(196,196,196))
        else:
            draw_aligned_line(target,(x+2,y+top_ind+ind*line_height,w-scrollbar_width-margin-4,line_height),"left",line,font)

    draw_indent(target,(x+w-scrollbar_width,y,scrollbar_width,h))
    

    c = (x+w-scrollbar_width/2-1,y+scrollbar_width/2+1) #центр стрелки
    size = ((scrollbar_width-6)/2,(scrollbar_width-4)/2)
    pg.draw.line(target,dark_color,(c[0]-size[0],c[1]+size[1]),(c[0]+size[0],c[1]+size[1]),2)
    pg.draw.line(target,dark_color,(c[0],c[1]-size[1]),(c[0]+size[0],c[1]+size[1]),2)
    pg.draw.line(target,light_color,(c[0]-size[0],c[1]+size[1]),(c[0],c[1]-size[1]),2)
    
    if m_state[2] and c[0]-size[0] <= m_state[0] <= c[0]+size[0] and c[1]-size[1] <= m_state[1] <= c[1]+size[1]:
        if scroll > 0:
            scroll -= 1
            
    c = (x+w-scrollbar_width/2-1,y+h-scrollbar_width/2-1) #центр стрелки
    size = ((scrollbar_width-6)/2,(scrollbar_width-4)/2)
    pg.draw.line(target,light_color,(c[0]-size[0],c[1]-size[1]),(c[0]+size[0],c[1]-size[1]),2)
    pg.draw.line(target,dark_color,(c[0],c[1]+size[1]),(c[0]+size[0],c[1]-size[1]),2)
    pg.draw.line(target,light_color,(c[0]-size[0],c[1]-size[1]),(c[0],c[1]+size[1]),2)
    if m_state[2] and c[0]-size[0] <= m_state[0] <= c[0]+size[0] and c[1]-size[1] <= m_state[1] <= c[1]+size[1]:
        if scroll+max_lines < len(items):
            scroll += 1

    if scroll+max_lines >= len(items): scroll = max(0, len(items)-max_lines)

    return [selection,scroll]

def draw_itemsel(target, rect, items, select, scroll, size, m_state):
    base_color = (196,196,196)
    light_color = (230,230,230)
    dark_color = (108,108,108)
    scrollbar_width = 18
    margin = 12
    x,y,w,h = rect

    max_per_w = int((w-(scrollbar_width+margin))/size)
    delimiter_w= (w-(scrollbar_width+margin)-max_per_w*size)/2
    max_per_ht = int(h/size)
    delimiter_ht = (h-max_per_ht*size)/2

    draw_indent(target,(x,y,w-(scrollbar_width+margin),h))

    for x_ind in range(max_per_w):
        for y_ind in range(max_per_ht):
            pointer = scroll+x_ind+y_ind*max_per_w
            if len(items) > pointer:
                surf = items[pointer]
                min_side = min(surf.get_size()) #о май гатто зис ис мисайде
                surf = pg.transform.scale(surf,(surf.get_width()*(size/min_side),surf.get_height()*(size/min_side)))
                surf =surf.subsurface(((surf.get_width()-size)/2,(surf.get_height()-size)/2,size,size))
                target.blit(surf,(x+delimiter_w+x_ind*size,y+delimiter_ht+size*y_ind))
                if 0 <= m_state[0] - (x+delimiter_w+x_ind*size) <= size and 0 <= m_state[1] - (y+delimiter_ht+size*y_ind) <= size and m_state[2]:
                    select = pointer if select != pointer else None
            if select == pointer:
                pg.draw.rect(target,(0,0,0),(x+delimiter_w+x_ind*size,y+delimiter_ht+size*y_ind,size,size),4)

    draw_indent(target,(x+w-scrollbar_width,y,scrollbar_width,h))

    c = (x+w-scrollbar_width/2-1,y+scrollbar_width/2+1) #центр стрелки
    size = ((scrollbar_width-6)/2,(scrollbar_width-4)/2)
    pg.draw.line(target,dark_color,(c[0]-size[0],c[1]+size[1]),(c[0]+size[0],c[1]+size[1]),2)
    pg.draw.line(target,dark_color,(c[0],c[1]-size[1]),(c[0]+size[0],c[1]+size[1]),2)
    pg.draw.line(target,light_color,(c[0]-size[0],c[1]+size[1]),(c[0],c[1]-size[1]),2)
    
    if m_state[2] and c[0]-size[0] <= m_state[0] <= c[0]+size[0] and c[1]-size[1] <= m_state[1] <= c[1]+size[1]:
        if scroll > 0:
            scroll -= max_per_w
            
    c = (x+w-scrollbar_width/2-1,y+h-scrollbar_width/2-1) #центр стрелки
    size = ((scrollbar_width-6)/2,(scrollbar_width-4)/2)
    pg.draw.line(target,light_color,(c[0]-size[0],c[1]-size[1]),(c[0]+size[0],c[1]-size[1]),2)
    pg.draw.line(target,dark_color,(c[0],c[1]+size[1]),(c[0]+size[0],c[1]-size[1]),2)
    pg.draw.line(target,light_color,(c[0]-size[0],c[1]-size[1]),(c[0],c[1]+size[1]),2)
    if m_state[2] and c[0]-size[0] <= m_state[0] <= c[0]+size[0] and c[1]-size[1] <= m_state[1] <= c[1]+size[1]:
        if scroll+max_per_ht*max_per_w < len(items):
            scroll += max_per_w

    if scroll+max_per_ht*max_per_w >= len(items)+max_per_w: scroll = max(0, len(items)-max_per_ht*max_per_w)

    return [select, scroll]

def draw_textbox(target, rect, text, font, state, unicode, m_state):
    x, y, w, h = rect

    draw_indent(target,(x+2,y+2,w-4,h-4),[210+30*state]*3)

    draw_aligned_line(target,(x+2,y+2,w-4,h-4),"textbox",text,font)

    if state:
        text += unicode["chars"]
        if unicode["backspace"]: text = text[:-1]
        if unicode["return"]+unicode["escape"]: state = False

    if m_state[2]:
        if x+2 <= m_state[0] <= x+w-2 and y+2 <= m_state[1] <= y+h-2:
            state = True
        else:
            state = False

    return text, state

def draw_imagebox(target,rect,image,scale,pos,m_state,selection = None):
    x, y, w, h = rect

    draw_indent(target, rect)

    temp_surf = pg.Surface((w-8,h-8),pg.SRCALPHA)

    return_info = False
    
    if image not in (None, ""):

        iw, ih = image.get_size()
        temp_surf.blit(pg.transform.scale(image, (iw*scale, ih*scale)), ((w-8-iw*scale)/2+pos[0], (h-8-ih*scale)/2+pos[1]))

        return_info = (x+8 <= m_state[0] <= x+w-8 and y+8 <= m_state[1] <= y+h-8)

        if selection != None:
            sx, sy, sw, sh = selection

            select_surf = pg.Surface((4,4),pg.SRCALPHA)
            select_surf.fill([240]*3)
            select_surf.set_alpha(32)
            pg.draw.rect(temp_surf,(240,240,240),((w-8-iw*scale)/2+pos[0]+sx*scale, (h-8-ih*scale)/2+pos[1]+sy*scale,sw*scale,sh*scale),2)
            temp_surf.blit(pg.transform.scale(select_surf,(sw*scale,sh*scale)),((w-8-iw*scale)/2+pos[0]+sx*scale, (h-8-ih*scale)/2+pos[1]+sy*scale))
            
            if return_info and m_state[2]:
                x1,y1,x2,y2 = sx, sy, sx+sw, sy+sh
                click_x = int((m_state[0]-x-4-((w-8-iw*scale)/2+pos[0]))/scale)
                click_y = int((m_state[1]-y-4-((h-8-ih*scale)/2+pos[1]))/scale)
                if m_state[4][0]:
                    if click_x < x2: x1 = click_x
                    elif click_x > x2: x1, x2 = x2, click_x
                    if click_y < y2: y1 = click_y
                    elif click_y > y2: y1, y2 = y2, click_y
                elif m_state[4][2]:
                    if click_x > x1: x2 = click_x
                    elif click_x < x1: x2, x1 = x1, click_x
                    if click_y > y1: y2 = click_y
                    elif click_y < y1:y2, y1 = y1, click_y
                selection = (x1,y1,x2-x1,y2-y1)

            return_info = (return_info, selection)
        target.blit(temp_surf, (x+4, y+4))

    return return_info

