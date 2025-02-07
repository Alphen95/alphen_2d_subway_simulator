#leitmotif "graphics" "library" for python, based on pygame.
#made by alphen95. credit author when used.
#style remotely based on Motif Window Manager, OpenMotif, Lesstif and CDE.
#всё, как у людей.

import pygame as pg

def draw_window(target,rect):
    base_color = (196,196,196)
    light_color = (230,230,230)
    dark_color = (108,108,108)

    shade = 2
    x,y,w,h = rect
    pg.draw.rect(target,base_color,(x,y,w,h))
    pg.draw.polygon(target,light_color,(
        (x,y),
        (x+w,y),(x+w-shade,y+shade),
        (x+shade,y+h-shade),(x,y+h)
    ))
    pg.draw.polygon(target,dark_color,(
        (x+w-shade,y+shade),(x+w,y),
        (x+w,y+h),
        (x,y+h),(x+shade,y+h-shade)
    ))
    pg.draw.rect(target,base_color,(x+shade,y+shade,w-shade*2,h-shade*2))


def draw_concavity(target,rect):
    base_color = (196,196,196)
    light_color = (108,108,108)
    dark_color = (230,230,230)

    shade = 2
    x,y,w,h = rect
    pg.draw.rect(target,base_color,(x,y,w,h))
    pg.draw.polygon(target,light_color,(
        (x,y),
        (x+w,y),(x+w-shade,y+shade),
        (x+shade,y+h-shade),(x,y+h)
    ))
    pg.draw.polygon(target,dark_color,(
        (x+w-shade,y+shade),(x+w,y),
        (x+w,y+h),
        (x,y+h),(x+shade,y+h-shade)
    ))
    pg.draw.rect(target,base_color,(x+shade,y+shade,w-shade*2,h-shade*2))


def draw_concavity_custom(target,rect,base_color,light_color,dark_color):
    shade = 2
    x,y,w,h = rect
    pg.draw.rect(target,base_color,(x,y,w,h))
    pg.draw.polygon(target,light_color,(
        (x,y),
        (x+w,y),(x+w-shade,y+shade),
        (x+shade,y+h-shade),(x,y+h)
    ))
    pg.draw.polygon(target,dark_color,(
        (x+w-shade,y+shade),(x+w,y),
        (x+w,y+h),
        (x,y+h),(x+shade,y+h-shade)
    ))
    pg.draw.rect(target,base_color,(x+shade,y+shade,w-shade*2,h-shade*2))


def draw_itemlist(target,rect,items,maxL,scroll,selected,font,lineheight,m_state):
    base_color = (196,196,196)
    light_color = (230,230,230)
    dark_color = (108,108,108)
    scrollbar_width = 18
    margin = 12
    x,y,w,h = rect
    drawable_lines = items[scroll:scroll+maxL]
    if len(drawable_lines) < maxL: drawable_lines += [""]*(maxL-len(drawable_lines))
    h = lineheight*maxL

    action = None

    draw_concavity(target,(x,y,w-(scrollbar_width+margin),h))

    for i, line in enumerate(drawable_lines):
        if line == selected:
            text = font.render(str(line),True,base_color)
            pg.draw.rect(target,(0,0,0),(x+4,y+lineheight*i+1,w-8-(scrollbar_width+margin),lineheight-2))
            if text.get_width() > w-4-(scrollbar_width+margin): text = text.subsurface(0,0,w-4-(scrollbar_width+margin),text.get_height())
            target.blit(text,(x+4,y+lineheight*(i+0.5)-text.get_height()/2))
        else:
            if m_state[2] and line != "":
                if x+4 <= m_state[0] <= x+4+w-8-(scrollbar_width+margin) and y+lineheight*i <= m_state[1] <= y+lineheight*(i+1): 
                    action = ["select",line]
            text = font.render(str(line),True,(0,0,0))
            if text.get_width() > w-4-(scrollbar_width+margin): text = text.subsurface(0,0,w-4-(scrollbar_width+margin),text.get_height())
            target.blit(text,(x+4,y+lineheight*(i+0.5)-text.get_height()/2))

    draw_concavity(target,(x+w-scrollbar_width,y,scrollbar_width,h))

    pg.draw.line(target,dark_color,(x+w-4,y+scrollbar_width-2),(x+w-scrollbar_width+2,y+scrollbar_width-2),2)
    pg.draw.line(target,dark_color,(x+w-4,y+scrollbar_width-2),(x+w-scrollbar_width/2-1,y+2),2)
    pg.draw.line(target,light_color,(x+w-scrollbar_width/2-1,y+2),(x+w-scrollbar_width+2,y+scrollbar_width-2),2)
    if m_state[2] and x+w-scrollbar_width <= m_state[0] <= x+w-2 and y <= m_state[1] <= y+scrollbar_width:
        action = ["scroll_up"]
        #print("zzz")
    
    pg.draw.line(target,light_color,(x+w-4,y+h-scrollbar_width+2),(x+w-scrollbar_width+2,y+h-scrollbar_width+2),2)
    pg.draw.line(target,dark_color,(x+w-4,y+h-scrollbar_width+2),(x+w-scrollbar_width/2-1,y+h-2),2)
    pg.draw.line(target,light_color,(x+w-scrollbar_width/2-1,y+h-2),(x+w-scrollbar_width+2,y+h-scrollbar_width+2),2)
    if m_state[2] and x+w-scrollbar_width <= m_state[0] <= x+w-2 and y+h-scrollbar_width <= m_state[1] <= y+h:
        action = ["scroll_down"]
        #print("aaa")

    return action


def draw_button(target,rect,aligment,text,font,m_state):
    x,y,w,h = rect

    act = None

    if (m_state[3] or m_state[2]) > 0 and x <= m_state[0] <= x+w and y <= m_state[1] <= y+h:
        if m_state[2]:
            act = "clicked"
        draw_concavity(target,(x+2,y+2,w-4,h-4))
    else:
        draw_window(target,(x+2,y+2,w-4,h-4))

    line = font.render(text,True,(0,0,0))
    if aligment == "left":
        if line.get_width() > w-6: line = line.subsurface(0,0,w-6,line.get_height())
        left_coord = x+3
    elif aligment == "right":
        if line.get_width() > w-6: line = line.subsurface(line.get_width()-(w-6),0,w-6,line.get_height())
        left_coord = x+w-line.get_width()
    else:
        if line.get_width() > w-6: line = line.subsurface((line.get_width()-(w-6))/2,0,w-6,line.get_height())
        left_coord = x+w/2-line.get_width()/2
     
    target.blit(line,(left_coord,y+h/2-line.get_height()/2))

    return act


def draw_label(target,rect,aligment,text,font):
    x,y,w,h = rect

    line = font.render(text,True,(0,0,0))
    if aligment == "left":
        if line.get_width() > w-6: line = line.subsurface(0,0,w-6,line.get_height())
        left_coord = x+3
    elif aligment == "right":
        if line.get_width() > w-6: line = line.subsurface(line.get_width()-(w-6),0,w-6,line.get_height())
        left_coord = x+w-line.get_width()
    else:
        if line.get_width() > w-6: line = line.subsurface((line.get_width()-(w-6))/2,0,w-6,line.get_height())
        left_coord = x+w/2-line.get_width()/2
     
    target.blit(line,(left_coord,y+h/2-line.get_height()/2))


def draw_textbox(target,rect,text,font,m_state,active):
    x,y,w,h = rect

    act = None

    if (m_state[3] or m_state[2]) > 0 and x <= m_state[0] <= x+w and y <= m_state[1] <= y+h:
        if m_state[2]:
            act = "clicked"

    draw_concavity_custom(target,(x+2,y+2,w-4,h-4),(210+30*active,210+30*active,210+30*active),(108,108,108),(230,230,230))

    line = font.render(str(text),True,(0,0,0))
    if line.get_width() > w-6: line = line.subsurface(line.get_width()-(w-6),0,w-6,line.get_height())
    left_coord = x+3
     
    target.blit(line,(left_coord,y+h/2-line.get_height()/2))

    return act

def draw_itemsel(target,rect,items,scroll,selected,lineheight,size,m_state):
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

    action = None

    draw_concavity(target,(x,y,w-(scrollbar_width+margin),h))

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
                    action = ["select",pointer if selected != pointer else None]
            if selected == pointer:
                pg.draw.rect(target,(0,0,0),(x+delimiter_w+x_ind*size,y+delimiter_ht+size*y_ind,size,size),4)

    draw_concavity(target,(x+w-scrollbar_width,y,scrollbar_width,h))

    pg.draw.line(target,dark_color,(x+w-4,y+scrollbar_width-2),(x+w-scrollbar_width+2,y+scrollbar_width-2),2)
    pg.draw.line(target,dark_color,(x+w-4,y+scrollbar_width-2),(x+w-scrollbar_width/2-1,y+2),2)
    pg.draw.line(target,light_color,(x+w-scrollbar_width/2-1,y+2),(x+w-scrollbar_width+2,y+scrollbar_width-2),2)
    if m_state[2] and x+w-scrollbar_width <= m_state[0] <= x+w-2 and y <= m_state[1] <= y+scrollbar_width:
        action = ["scroll_up",max_per_w]
        #print("zzz")
    
    pg.draw.line(target,light_color,(x+w-4,y+h-scrollbar_width+2),(x+w-scrollbar_width+2,y+h-scrollbar_width+2),2)
    pg.draw.line(target,dark_color,(x+w-4,y+h-scrollbar_width+2),(x+w-scrollbar_width/2-1,y+h-2),2)
    pg.draw.line(target,light_color,(x+w-scrollbar_width/2-1,y+h-2),(x+w-scrollbar_width+2,y+h-scrollbar_width+2),2)
    if m_state[2] and x+w-scrollbar_width <= m_state[0] <= x+w-2 and y+h-scrollbar_width <= m_state[1] <= y+h:
        action = ["scroll_down",max_per_w,max_per_ht]
        #print("aaa")

    return action

if __name__ == "__main__":
    print("Nope, you're in the wrong place. Check out the main.py file in the parent directory, or notify @alphen95 if this was shipped NOT with AISS.\n'Copyright' @alphen95 2020-IDK. Вечность пахнет нефтью!")