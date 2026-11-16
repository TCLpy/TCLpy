local ffi = require("ffi")

ffi.cdef[[
    typedef struct cs_insn {
        unsigned int id;
        uint64_t address;
        uint16_t size;
        uint8_t bytes[24];
        char mnemonic[32];
        char op_str[160];
        void *detail;
    } cs_insn;

    int cs_open(int arch, int mode, size_t *handle);
    size_t cs_disasm(
        size_t handle,
        const uint8_t *code,
        size_t code_size,
        uint64_t address,
        size_t count,
        cs_insn **insn
    );
    int cs_close(size_t *handle);
    void cs_free(cs_insn *insn, size_t count);
]]

local cs = ffi.load("capstone")
assert(ffi.sizeof("cs_insn") == 248, "cs_insn size mismatch")

return {
    cs          = cs,
    CS_ARCH_X86 = 3,
    CS_MODE_64  = 8
}
