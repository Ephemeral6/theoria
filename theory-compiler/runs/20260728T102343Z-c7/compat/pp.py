import os, sys
SRC, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path.insert(0, SRC); os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "..","..","..","tests","fixtures")
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.parser.playbook_parser import parse_playbook
from theory_compiler.parser.pretty_printer import print_theory, print_playbook
def w(n,t):
    open(os.path.join(OUT,n),"w",encoding="utf-8",newline="\n").write(t)
for lbl,f in (("peg5","peg_theory.dsl"),("peg4","peg4_theory.dsl")):
    w(lbl+".pp.dsl", print_theory(parse_theory(open(os.path.join(FIX,f),encoding="utf-8").read())))
w("peg_playbook.pp.dsl", print_playbook(parse_playbook(open(os.path.join(FIX,"peg_playbook.dsl"),encoding="utf-8").read())))
print("ok")
