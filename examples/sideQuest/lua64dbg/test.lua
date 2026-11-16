local ffi = require("ffi")

ffi.cdef[[
typedef struct cs_insn {
        unsigned int id;
        uint64_t address;
        uint16_t size;
        uint8_t bytes[24];
        char mnemonic[32];
        char op_str[160];
        bool is_alias;
        uint64_t alias_id;
        bool usesAliasDetails;
        void *detail;
    } cs_insn;

    int cs_open(int arch, int mode, size_t *handle);
    int cs_option(size_t handle, int type, size_t value);
    size_t cs_disasm(size_t handle, const uint8_t *code, size_t code_size, uint64_t address, size_t count, cs_insn **insn);
    int cs_close(size_t *handle);
    void cs_free(cs_insn *insn, size_t count);
]]

local cs = ffi.load("capstone")

local CS_ARCH_X86   = 3
local CS_MODE_32    = 4
local CS_ERR_OK     = 0
local CS_OPT_DETAIL = 2
local CS_OPT_ON     = 3

local X86Code32 = "\x8d\x4c\x32\x08\x01\xd8\x81\xc6\x34\x12\x00\x00\x05\x23\x01\x00\x00\x36\x8b\x84\x91\x23\x01\x00\x00\x41\x8d\x84\x39\x89\x67\x00\x00\x8d\x87\x89\x67\x00\x00\xb4\xc6"

local handle = ffi.new("size_t[1]")
local err = cs.cs_open(CS_ARCH_X86, CS_MODE_32, handle)

if err == CS_ERR_OK then
    print("Capstone Loaded")
else
    error("Failed to load Capstone, error code: " .. tostring(err))
end

cs.cs_option(handle[0], CS_OPT_DETAIL, CS_OPT_ON)

local insn = ffi.new("cs_insn*[1]")
local count = tonumber(cs.cs_disasm(handle[0], X86Code32, #X86Code32, 0x00400000, 0, insn))
print("Disassembled " .. count .. " instructions")

for i = 0, count - 1 do
    local ins = insn[0][i]
    print(string.format(
        "%08X %-8s %s",
        tonumber(ins.address),
        string.upper(ffi.string(ins.mnemonic)),
        ffi.string(ins.op_str)
    ))
end

if count > 0 then
    cs.cs_free(insn[0], count)
end
cs.cs_close(handle)
print("Capstone Unloaded")
