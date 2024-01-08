// Copyright 2023 Brandon Matthews <thenewwazoo@optimaltour.us>
// All rights reserved. GPLv3 License

void homekit_task_entry(void* ctx);

void notify_homekit_target_door_state_change();
void notify_homekit_current_door_state_change();
void notify_homekit_active();
void notify_homekit_target_lock();
void notify_homekit_current_lock();
void notify_homekit_obstruction();
void notify_homekit_light();
void notify_homekit_motion();
