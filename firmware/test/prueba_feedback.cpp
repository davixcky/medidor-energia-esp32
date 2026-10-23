#include "../lib/feedback/feedback.h"
#include <cassert>
#include <cstdio>
int main() {
  feedback::Sound s;
  assert(!s.tick(0, false));
  s.click(10); assert(s.tick(10,false)); assert(!s.tick(40,false));
  assert(s.tick(100,true)); assert(!s.tick(180,true));
  assert(s.tick(260,true)); assert(!s.tick(340,true));
  assert(!s.tick(1000,true)); // persistent alarm does not keep beeping
  s.tick(1010,false); assert(s.tick(1020,true));
  assert(!s.tick(1030,false)); // acknowledgment cancels remaining tones
  s.toggle(); assert(!s.tick(1100,true));
  s.toggle(); assert(!s.tick(1110,true)); // unmute does not replay an existing alarm
  s.tick(1120,false); assert(s.tick(1130,true));
  s.stop(); s.tick(1140,false);
  s.click(UINT32_MAX-10); assert(s.tick(5,false)); assert(!s.tick(20,false));
  puts("Feedback: button, alert, acknowledge, mute and rollover passed");
}
