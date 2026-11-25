#include "../lib/ajustes/ajustes.h"
#include <cassert>
#include <cstdio>
int main() {
 using namespace ajustes_ui;
 int edges=0; int cw[]={0,1,3,2,0};
 for(int i=1;i<5;i++)edges+=transition(cw[i-1],cw[i]);
 assert(edges==4);
 for(int i=4;i>0;i--)edges+=transition(cw[i],cw[i-1]);
 assert(edges==0);
 assert(transition(0,3)==0 && transition(1,2)==0);
 assert(transition(0,1)+transition(1,0)==0); // contact bounce cancels
 Menu m; assert(!m.press() && m.active);assert(!m.press() && m.editing);
 m.turn(-100);assert(m.draft.brightness==32 && m.values.brightness==200);
 m.cancel();assert(!m.editing && m.values.brightness==200);
 m.press();m.turn(100);assert(m.press() && m.values.brightness==255);
 m.turn(1);m.press();m.turn(1);assert(m.press() && m.values.muted);
 m.turn(1);m.press();m.turn(-1000);assert(m.press() && m.values.threshold==100);
 m.press();m.turn(1000);assert(m.press() && m.values.threshold==10000);
 m.turn(1);assert(!m.press() && !m.active);
 puts("Encoder: direction, bounce, invalid edges; menu: cancel, save, limits passed");
}
