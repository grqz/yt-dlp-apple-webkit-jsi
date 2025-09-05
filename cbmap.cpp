#include <map>
#include "cbmap.h"

extern "C" {

typedef struct c_cb_st {
    user_callback_type callback;
    void *userData;
} CCb;

typedef std::map<void *, CCb> MapImplType;
struct callback_map_st : public MapImplType {
    using MapImplType::MapImplType;
};

CallbackMap *cbmap_new(void) {
    return new CallbackMap;
}
unsigned char cbmap_add(CallbackMap *cbmap, void *k, user_callback_type fnptr, void *userData) {
    return static_cast<unsigned char>(cbmap->insert_or_assign(k, CCb{fnptr, userData}).second);
}
void cbmap_call(const CallbackMap *cbmap, void *k, void *ctx) {
    if (auto it = cbmap->find(k); it != cbmap->end())
        it->second.callback(ctx, it->second.userData);
}
void cbmap_callpop(CallbackMap *cbmap, void *k, void *ctx) {
    if (auto it = cbmap->find(k); it != cbmap->end()) {
        it->second.callback(ctx, it->second.userData);
        cbmap->erase(it);
    }
}
unsigned char cbmap_rm(CallbackMap *cbmap, void *k) {
    return static_cast<unsigned char>(cbmap->erase(k));
}
CallbackMap *cbmap_copy(const CallbackMap *cbmap) {
    return new CallbackMap(*cbmap);
}
CallbackMap *cbmap_move(const CallbackMap *cbmap) {
    return new CallbackMap(std::move(*cbmap));
}
void cbmap_free(CallbackMap *cbmap) {
    delete cbmap;
}

}  // extern "C"
