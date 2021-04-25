#------------------------------------------------
# Usage examples:
# ---------------
#   make
#   make debug
#   make cc=g++-8
#   make cc=clang++ all
#------------------------------------------------

CC_DEFAULT = c++
CMAKE_GEN  = ../../..

ifdef cc
	CMAKE_GEN += -DCMAKE_CXX_COMPILER=$(cc)
else
	cc = $(CC_DEFAULT)
endif

SUB_DIR    = make-$(notdir $(cc))

CMAKE_REL  = $(CMAKE_GEN) -DCMAKE_BUILD_TYPE=Release
CMAKE_DBG  = $(CMAKE_GEN) -DCMAKE_BUILD_TYPE=Debug
CMAKE_RDBG = $(CMAKE_GEN) -DCMAKE_BUILD_TYPE=RelWithDebInfo
CMAKE_RMIN = $(CMAKE_GEN) -DCMAKE_BUILD_TYPE=MinSizeRel

default: release

all:     release debug relwithdebinfo minsizerel

release:
	@mkdir   -p       build/$(SUB_DIR)/release;        \
	 cd               build/$(SUB_DIR)/release;        cmake $(CMAKE_REL) 
	@$(MAKE) -s -j -C build/$(SUB_DIR)/release

debug:
	@mkdir   -p       build/$(SUB_DIR)/debug;          \
	 cd               build/$(SUB_DIR)/debug;          cmake $(CMAKE_DBG)
	@$(MAKE) -s -j -C build/$(SUB_DIR)/debug

relwithdebinfo:
	@mkdir   -p       build/$(SUB_DIR)/relwithdebinfo; \
	 cd               build/$(SUB_DIR)/relwithdebinfo; cmake $(CMAKE_RDBG)
	@$(MAKE) -s -j -C build/$(SUB_DIR)/relwithdebinfo

minsizerel:
	@mkdir   -p       build/$(SUB_DIR)/minsizerel;     \
	 cd               build/$(SUB_DIR)/minsizerel;     cmake $(CMAKE_RMIN)
	@$(MAKE) -s -j -C build/$(SUB_DIR)/minsizerel

clean:
	@rm -rf   build/$(SUB_DIR)

realclean:
	@rm -rf   bin
	@rm -rf   build
