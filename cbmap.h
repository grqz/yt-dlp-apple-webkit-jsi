#ifndef CBMAP_H
#define CBMAP_H

#ifdef __cplusplus
extern "C" {
#endif

struct callback_map_st;
typedef struct callback_map_st CallbackMap;
typedef void (*user_callback_type)(void *ctx, void *userData);

CallbackMap *cbmap_new(void);
// Return value: 1 for success, 0 when the value is overwritten
unsigned char cbmap_add(CallbackMap *cbmap, void *k, user_callback_type fnptr, void *userData);
void cbmap_call(const CallbackMap *cbmap, void *k, void *ctx);
void cbmap_callpop(CallbackMap *cbmap, void *k, void *ctx);
// Return value: 1 for success, 0 when the value is not found
unsigned char cbmap_rm(CallbackMap *cbmap, void *k);
CallbackMap *cbmap_copy(const CallbackMap *cbmap);
CallbackMap *cbmap_move(const CallbackMap *cbmap);
void cbmap_free(CallbackMap *cbmap);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // CBMAP_H
