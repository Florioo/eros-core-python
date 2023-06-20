from blessed import Terminal

term = Terminal()

print(term.home + term.clear + term.move_y(term.height // 2))
print(term.black_on_darkkhaki(term.center('press any key to continue.')))

with term.cbreak(), term.hidden_cursor():
    while True:
        # val = term.inkey(timeout=5)
        # if val:
        #     break
        # print(term.move_down + term.center('press any key to continue.'))
        inp = term.inkey()  
        print(inp)
    

# print(term.move_down(2) + 'You pressed ' + term.bold(repr(inp)))