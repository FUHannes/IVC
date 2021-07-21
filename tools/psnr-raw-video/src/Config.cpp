

#include "Config.h"


struct MatchPathSeparator{ bool operator()( char c ) const { return ( c == '\\' || c == '/' ); } };
std::string baseNameFromPath( const std::string& path )
{
  return std::string( std::find_if( path.rbegin(), path.rend(), MatchPathSeparator() ).base(), path.end() );
}

Message ConfigPars::usage() const
{
  Message m;
#if 1 // simplify
  m << "\nUsage:\n\n"
    << "> " << m_progName << " " << "<w> <h> <cf> <org> <rec> [ <strm> <fps> ]\n\n"
    << "     w : frame width in luma samples\n"
    << "     h : frame height in luma samples\n"
    << "    cf : chroma format [400|420|422|444]\n"
    << "   org : file name of original video\n"
    << "   rec : file name of reconstructed video\n"
    << "  strm : filename of bitstream\n"
    << "   fps : frame rate of original video\n"
    << "\n";
#else
  m << "\nUsage:\n\n"
    << "> " << m_progName << " " << "<w> <h> <cf> <bo> <org> <br> <rec> [ <s0> <sk> [ <strm> <fps> ][ <strg> ] ]\n\n"
    << "     w : frame width in luma samples\n"
    << "     h : frame height in luma samples\n"
    << "    cf : chroma format [400|420|422|444]\n"
    << "    bo : bit depth of original video [8..12]\n"
    << "    br : bit depth of reconstructed video [8..12]\n"
    << "   org : file name of original video\n"
    << "   rec : file name of reconstructed video\n"
    << "    s0 : number of frames to skip at beginning of original video\n"
    << "    sk : number of frames to skip between frames of original video\n"
    << "  strm : filename of bitstream\n"
    << "   fps : frame rate of original video\n"
    << "  strg : prefix string for summary output\n"
    << "\n";
#endif
  return m;
}

void ConfigPars::parseError( const Message& err ) const
{
  Message msg( "\nERROR: " );
  msg << err << "\n" << usage();
  throw msg;
}


#if 1 // simplify
ConfigPars::ConfigPars( const int argc, const char** argv )
{
#define PERR(c,m) if(c) { Message msg; msg << m; parseError(msg); }

  // check for simd restrictions (not documented)
  SIMDMode maxSIMD = SIMDMode(ENABLE_SIMD);
  if( std::string( argv[argc-1] ) == "nosimd" || std::string( argv[argc-1] ) == "nosse" )
  {
    maxSIMD = std::min<SIMDMode>( maxSIMD, SIMD_SCALAR );
    const_cast<int&>(argc)--;
  }
  else if( std::string( argv[argc-1] ) == "noavx" || std::string( argv[argc-1] ) == "noavx2" )
  {
    maxSIMD = std::min<SIMDMode>( maxSIMD, SIMD_SSE41 );
    const_cast<int&>(argc)--;
  }

  // init
  bool        nerr  = false;
  int         arg   = 0;
  int         w     = 0;
  int         h     = 0;
  std::string cf    = "";
  int         bo    = 8;
  std::string org   = "";
  int         br    = 8;
  std::string rec   = "";
  int         s0    = 0;
  int         sk    = 0;
  std::string strm  = "";
  double      fps   = 1.0;
  std::string strg  = "";

  // parse
  m_progName  = baseNameFromPath( argv[ arg++ ] );
  if( !nerr && argc - arg >= 5 )
  {
    w         = atoi( argv[ arg++ ] );
    h         = atoi( argv[ arg++ ] );
    cf        =       argv[ arg++ ];
    org       =       argv[ arg++ ];
    rec       =       argv[ arg++ ];
  }
  else
  {
    nerr      = true;
  }
  nerr        = ( nerr || ( argc - arg > 0 && argc - arg < 2 ) );
  if( !nerr && argc - arg >= 2 )
  {
    strm      =       argv[ arg++ ];
    fps       = atof( argv[ arg++ ] );
  }
  nerr        = ( nerr || argc - arg > 0 );

  // basic checks
  PERR( nerr,                                                         "This tool cannot be used with " << argc-1 << " arguments" );
  PERR( w <= 0 || w > (1<<15),                                        "Width must be in range [1;" << (1<<15) << "]" );
  PERR( h <= 0 || h > (1<<15),                                        "Height must be in range [1;" << (1<<15) << "]" );
  PERR( cf != "400" && cf != "420" && cf != "422" && cf != "444",     "Chroma format must be equal to 400, 420, 422, or 444" );
  PERR( ( cf == "420" || cf == "422") && (w&1),                       "For 420 or 422 video, width must be a multiple of 2" );
  PERR( cf == "420" && (h&1),                                         "For 420 video, height must be a multiple of 2" );
  PERR( bo < 8 || bo > 12 || br < 8 || br > 12,                       "Bit depth must be in range [8;12]" );
  PERR( org.empty() || rec.empty(),                                   "Video file names must not be empty" );
  PERR( s0 < 0 || sk < 0,                                             "Frame skips cannot be less than 0" );
  PERR( fps <= 0.0,                                                   "Frame rate cannot be less than or equal to 0" );

  // intermediate parameters and checks
  const unsigned  cShift          = ( cf == "444" ? 0 : cf == "422" ? 1 : cf == "420" ? 2 : sizeof(std::size_t)<<3 );
  std::size_t     bytesPerFrmOrg  = 0;
  std::size_t     bytesPerFrmRec  = 0;
  std::size_t     numFrames       = 0;
  double          bitrate         = 0.0;
  {
    std::size_t   numSamplesY     = std::size_t( w * h );
    std::size_t   numSamplesFrm   = numSamplesY + ( cf=="400" ? 0 : ( numSamplesY >> cShift ) << 1 );
    bytesPerFrmOrg                = numSamplesFrm * ( bo == 8 ? 1 : 2 );
    bytesPerFrmRec                = numSamplesFrm * ( br == 8 ? 1 : 2 );
    std::ifstream orgVideoFile    ( org, std::ios::in | std::ios::binary );
    std::ifstream recVideoFile    ( rec, std::ios::in | std::ios::binary );
    PERR( !orgVideoFile.is_open(),                                    "Cannot open original video file \"" << org << "\"" );
    PERR( !recVideoFile.is_open(),                                    "Cannot open reconstructed video file \"" << rec << "\"" );
    orgVideoFile.seekg( 0, std::ios::end );
    recVideoFile.seekg( 0, std::ios::end );
    std::size_t   numOrgBytes     = std::size_t( orgVideoFile.tellg() );
    std::size_t   numRecBytes     = std::size_t( recVideoFile.tellg() );
    orgVideoFile.close();
    recVideoFile.close();
    PERR( numOrgBytes == 0,                                           "Original video file \"" << org << "\" is empty" );
    PERR( numRecBytes == 0,                                           "Reconstructed video file \"" << rec << "\" is empty" );
    std::size_t   nomFramesOrg    = numOrgBytes / bytesPerFrmOrg;
    std::size_t   nomFramesRec    = numRecBytes / bytesPerFrmRec;
    PERR( nomFramesOrg * bytesPerFrmOrg != numOrgBytes,               "Original video file \"" << org << "\" contains a non-integral number of frames" );
    PERR( nomFramesRec * bytesPerFrmRec != numRecBytes,               "Reconstructed video file \"" << rec << "\" contains a non-integral number of frames" );
    std::size_t   reqFramesOrg    = (nomFramesRec-1)*(1+sk) + (1+s0);
    PERR( nomFramesOrg < reqFramesOrg,                                "Original video file \"" << org << "\" contains less frames than reconstructed video file \"" << rec << "\" (when considering skipped frames)" );
    numFrames                     = nomFramesRec;
  }
  if( !strm.empty() )
  {
    std::ifstream bitstreamFile   ( strm, std::ios::in | std::ios::binary );
    PERR( !bitstreamFile.is_open(),                                   "Cannot open bitstream file \"" << strm << "\"" );
    bitstreamFile.seekg( 0, std::ios::end );
    std::size_t   numStrBytes     = std::size_t( bitstreamFile.tellg() );
    bitstreamFile.close();
    PERR( numStrBytes == 0,                                           "Bitstream file \"" << strm << "\" is empty" );
    bitrate                       = double( numStrBytes << 3 ) * fps / double( numFrames*1000*(1+sk) );
  }

  // set parameters
  m_fileName        [ORG]     = org;
  m_fileName        [REC]     = rec;
  m_numComp                   = ( cf == "400" ? 1 : 3 );
  m_numSamples           [0]  = unsigned(w) * unsigned(h);
  m_numSamples           [1]  = ( cf == "400" ? 0 : m_numSamples[0] >> cShift );
  m_numSamples           [2]  = m_numSamples[1];
  m_bytesPerSample  [ORG][0]  = ( bo == 8 ? 1 : 2 );
  m_bytesPerSample  [ORG][1]  = m_bytesPerSample[ORG][0];
  m_bytesPerSample  [ORG][2]  = m_bytesPerSample[ORG][1];
  m_bytesPerSample  [REC][0]  = ( br == 8 ? 1 : 2 );
  m_bytesPerSample  [REC][1]  = m_bytesPerSample[REC][0];
  m_bytesPerSample  [REC][2]  = m_bytesPerSample[REC][1];
  m_bitdepth        [ORG][0]  = bo;
  m_bitdepth        [ORG][1]  = m_bitdepth[ORG][0];
  m_bitdepth        [ORG][2]  = m_bitdepth[ORG][1];
  m_bitdepth        [REC][0]  = br;
  m_bitdepth        [REC][1]  = m_bitdepth[REC][0];
  m_bitdepth        [REC][2]  = m_bitdepth[REC][1];
  m_skipBytes       [ORG][0]  = std::size_t(s0) * bytesPerFrmOrg;
  m_skipBytes       [ORG][1]  = std::size_t(sk) * bytesPerFrmOrg;
  m_skipBytes       [REC][0]  = std::size_t( 0) * bytesPerFrmRec;
  m_skipBytes       [REC][1]  = std::size_t( 0) * bytesPerFrmRec;
  m_numFrames                 = numFrames;
  m_bitrate                   = bitrate;
  m_prefixString              = strg;

  // simd and memory alignment and size
  static const std::string    simdStr  [SIMD_NUM_VALUES] = { "", "SSE4.1", "AVX2" };
  static const std::size_t    simdAlign[SIMD_NUM_VALUES] = {  1,       16,     32 };
  m_SIMDMode                  = getSIMD( maxSIMD );
  m_memAlignment              = simdAlign[m_SIMDMode];
  m_memSizeRequired [ORG]     = bytesPerFrmOrg + ( m_memAlignment << 2 );
  m_memSizeRequired [REC]     = bytesPerFrmRec + ( m_memAlignment << 2 );

  // output
  std::cout << "PSNR tool (version 0.71)";
  if( !simdStr[m_SIMDMode].empty() )
  {
    std::cout << " [" << simdStr[m_SIMDMode] << "]";
  }
  std::cout << std::endl << std::endl;
}
#else
ConfigPars::ConfigPars( const int argc, const char** argv )
{
#define PERR(c,m) if(c) { Message msg; msg << m; parseError(msg); }

  // check for simd restrictions (not documented)
  SIMDMode maxSIMD = SIMDMode(ENABLE_SIMD);
  if( std::string( argv[argc-1] ) == "nosimd" || std::string( argv[argc-1] ) == "nosse" )
  {
    maxSIMD = std::min<SIMDMode>( maxSIMD, SIMD_SCALAR );
    const_cast<int&>(argc)--;
  }
  else if( std::string( argv[argc-1] ) == "noavx" || std::string( argv[argc-1] ) == "noavx2" )
  {
    maxSIMD = std::min<SIMDMode>( maxSIMD, SIMD_SSE41 );
    const_cast<int&>(argc)--;
  }

  // init
  bool        nerr  = false;
  int         arg   = 0;
  int         w     = 0;
  int         h     = 0;
  std::string cf    = "";
  int         bo    = 0;
  std::string org   = "";
  int         br    = 0;
  std::string rec   = "";
  int         s0    = 0;
  int         sk    = 0;
  std::string strm  = "";
  double      fps   = 1.0;
  std::string strg  = "";

  // parse
  m_progName  = baseNameFromPath( argv[ arg++ ] );
  if( !nerr && argc - arg >= 7 )
  {
    w         = atoi( argv[ arg++ ] );
    h         = atoi( argv[ arg++ ] );
    cf        =       argv[ arg++ ];
    bo        = atoi( argv[ arg++ ] );
    org       =       argv[ arg++ ];
    br        = atoi( argv[ arg++ ] );
    rec       =       argv[ arg++ ];
  }
  else
  {
    nerr      = true;
  }
  nerr        = ( nerr || ( argc - arg > 0 && argc - arg < 2 ) );
  if( !nerr && argc - arg >= 2 )
  {
    s0        = atoi( argv[ arg++ ] );
    sk        = atoi( argv[ arg++ ] );
  }
  if( !nerr && argc - arg >= 2 )
  {
    strm      =       argv[ arg++ ];
    fps       = atof( argv[ arg++ ] );
  }
  if( !nerr && argc - arg >= 1 )
  {
    strg      =       argv[ arg++ ];
  }
  nerr        = ( nerr || argc - arg > 0 );

  // basic checks
  PERR( nerr,                                                         "This tool cannot be used with " << argc-1 << " arguments" );
  PERR( w <= 0 || w > (1<<15),                                        "Width must be in range [1;" << (1<<15) << "]" );
  PERR( h <= 0 || h > (1<<15),                                        "Height must be in range [1;" << (1<<15) << "]" );
  PERR( cf != "400" && cf != "420" && cf != "422" && cf != "444",     "Chroma format must be equal to 400, 420, 422, or 444" );
  PERR( ( cf == "420" || cf == "422") && (w&1),                       "For 420 or 422 video, width must be a multiple of 2" );
  PERR( cf == "420" && (h&1),                                         "For 420 video, height must be a multiple of 2" );
  PERR( bo < 8 || bo > 12 || br < 8 || br > 12,                       "Bit depth must be in range [8;12]" );
  PERR( org.empty() || rec.empty(),                                   "Video file names must not be empty" );
  PERR( s0 < 0 || sk < 0,                                             "Frame skips cannot be less than 0" );
  PERR( fps <= 0.0,                                                   "Frame rate cannot be less than or equal to 0" );

  // intermediate parameters and checks
  const unsigned  cShift          = ( cf == "444" ? 0 : cf == "422" ? 1 : cf == "420" ? 2 : sizeof(std::size_t)<<3 );
  std::size_t     bytesPerFrmOrg  = 0;
  std::size_t     bytesPerFrmRec  = 0;
  std::size_t     numFrames       = 0;
  double          bitrate         = 0.0;
  {
    std::size_t   numSamplesY     = std::size_t( w * h );
    std::size_t   numSamplesFrm   = numSamplesY + ( ( numSamplesY >> cShift ) << 1 );
    bytesPerFrmOrg                = numSamplesFrm * ( bo == 8 ? 1 : 2 );
    bytesPerFrmRec                = numSamplesFrm * ( br == 8 ? 1 : 2 );
    std::ifstream orgVideoFile    ( org, std::ios::in | std::ios::binary );
    std::ifstream recVideoFile    ( rec, std::ios::in | std::ios::binary );
    PERR( !orgVideoFile.is_open(),                                    "Cannot open original video file \"" << org << "\"" );
    PERR( !recVideoFile.is_open(),                                    "Cannot open reconstructed video file \"" << rec << "\"" );
    orgVideoFile.seekg( 0, std::ios::end );
    recVideoFile.seekg( 0, std::ios::end );
    std::size_t   numOrgBytes     = std::size_t( orgVideoFile.tellg() );
    std::size_t   numRecBytes     = std::size_t( recVideoFile.tellg() );
    orgVideoFile.close();
    recVideoFile.close();
    PERR( numOrgBytes == 0,                                           "Original video file \"" << org << "\" is empty" );
    PERR( numRecBytes == 0,                                           "Reconstructed video file \"" << rec << "\" is empty" );
    std::size_t   nomFramesOrg    = numOrgBytes / bytesPerFrmOrg;
    std::size_t   nomFramesRec    = numRecBytes / bytesPerFrmRec;
    PERR( nomFramesOrg * bytesPerFrmOrg != numOrgBytes,               "Original video file \"" << org << "\" contains a non-integral number of frames" );
    PERR( nomFramesRec * bytesPerFrmRec != numRecBytes,               "Reconstructed video file \"" << rec << "\" contains a non-integral number of frames" );
    std::size_t   reqFramesOrg    = (nomFramesRec-1)*(1+sk) + (1+s0);
    PERR( nomFramesOrg < reqFramesOrg,                                "Original video file \"" << org << "\" contains less frames than reconstructed video file \"" << rec << "\" (when considering skipped frames)" );
    numFrames                     = nomFramesRec;
  }
  if( !strm.empty() )
  {
    std::ifstream bitstreamFile   ( strm, std::ios::in | std::ios::binary );
    PERR( !bitstreamFile.is_open(),                                   "Cannot open bitstream file \"" << strm << "\"" );
    bitstreamFile.seekg( 0, std::ios::end );
    std::size_t   numStrBytes     = std::size_t( bitstreamFile.tellg() );
    bitstreamFile.close();
    PERR( numStrBytes == 0,                                           "Bitstream file \"" << strm << "\" is empty" );
    bitrate                       = double( numStrBytes << 3 ) * fps / double( numFrames*1000*(1+sk) );
  }

  // set parameters
  m_fileName        [ORG]     = org;
  m_fileName        [REC]     = rec;
  m_numComp                   = ( cf == "400" ? 1 : 3 );
  m_numSamples           [0]  = unsigned(w) * unsigned(h);
  m_numSamples           [1]  = m_numSamples[0] >> cShift;
  m_numSamples           [2]  = m_numSamples[1];
  m_bytesPerSample  [ORG][0]  = ( bo == 8 ? 1 : 2 );
  m_bytesPerSample  [ORG][1]  = m_bytesPerSample[ORG][0];
  m_bytesPerSample  [ORG][2]  = m_bytesPerSample[ORG][1];
  m_bytesPerSample  [REC][0]  = ( br == 8 ? 1 : 2 );
  m_bytesPerSample  [REC][1]  = m_bytesPerSample[REC][0];
  m_bytesPerSample  [REC][2]  = m_bytesPerSample[REC][1];
  m_bitdepth        [ORG][0]  = bo;
  m_bitdepth        [ORG][1]  = m_bitdepth[ORG][0];
  m_bitdepth        [ORG][2]  = m_bitdepth[ORG][1];
  m_bitdepth        [REC][0]  = br;
  m_bitdepth        [REC][1]  = m_bitdepth[REC][0];
  m_bitdepth        [REC][2]  = m_bitdepth[REC][1];
  m_skipBytes       [ORG][0]  = std::size_t(s0) * bytesPerFrmOrg;
  m_skipBytes       [ORG][1]  = std::size_t(sk) * bytesPerFrmOrg;
  m_skipBytes       [REC][0]  = std::size_t( 0) * bytesPerFrmRec;
  m_skipBytes       [REC][1]  = std::size_t( 0) * bytesPerFrmRec;
  m_numFrames                 = numFrames;
  m_bitrate                   = bitrate;
  m_prefixString              = strg;

  // simd and memory alignment and size
  static const std::string    simdStr  [SIMD_NUM_VALUES] = { "", "SSE4.1", "AVX2" };
  static const std::size_t    simdAlign[SIMD_NUM_VALUES] = {  1,       16,     32 };
  m_SIMDMode                  = getSIMD( maxSIMD );
  m_memAlignment              = simdAlign[m_SIMDMode];
  m_memSizeRequired [ORG]     = bytesPerFrmOrg + ( m_memAlignment << 2 );
  m_memSizeRequired [REC]     = bytesPerFrmRec + ( m_memAlignment << 2 );

  // output
  std::cout << "PSNR tool (version 0.71)";
  if( !simdStr[m_SIMDMode].empty() )
  {
    std::cout << " [" << simdStr[m_SIMDMode] << "]";
  }
  std::cout << std::endl << std::endl;
}
#endif


#if ENABLE_SIMD

#if defined(__GNUC__) && !defined(__clang__)
#    define GCC_VERSION_AT_LEAST(x,y) (__GNUC__ > x || __GNUC__ == x && __GNUC_MINOR__ >= y)
#else
#    define GCC_VERSION_AT_LEAST(x,y) 0
#endif

#ifdef __clang__
#    define CLANG_VERSION_AT_LEAST(x,y) (__clang_major__ > x || __clang_major__ == x && __clang_minor__ >= y)
#else
#    define CLANG_VERSION_AT_LEAST(x,y) 0
#endif

#if defined ( __MINGW32__ ) && !defined (  __MINGW64__ )
# define SIMD_UP_TO_SSE42 1
#else
# define SIMD_UP_TO_SSE42 0
#endif

#if defined( _WIN32 ) && !defined( __MINGW32__ )
#include <intrin.h>
#define do_cpuid    __cpuid
#define do_cpuidex  __cpuidex
#else
#include <cpuid.h>
void do_cpuid(int CPUInfo[4], int InfoType)
{
  __get_cpuid( (unsigned)InfoType, (unsigned*)&CPUInfo[0], (unsigned*)&CPUInfo[1], (unsigned*)&CPUInfo[2], (unsigned*)&CPUInfo[3] );
}
#if !SIMD_UP_TO_SSE42
#define do_cpuidex(cd, v0, v1) __cpuid_count(v0, v1, cd[0], cd[1], cd[2], cd[3])
#endif
#endif

static inline int64_t xgetbv (int ctr) 
{
#if (defined (_MSC_FULL_VER) && _MSC_FULL_VER >= 160040000) || (defined (__INTEL_COMPILER) && __INTEL_COMPILER >= 1200) // Microsoft or Intel compiler supporting _xgetbv intrinsic
  return _xgetbv(ctr);                                   // intrinsic function for XGETBV
#elif defined(__GNUC__)                                    // use inline assembly, Gnu/AT&T syntax
  uint32_t a, d;
#if GCC_VERSION_AT_LEAST(4,4) || CLANG_VERSION_AT_LEAST(3,3)
  __asm("xgetbv" : "=a"(a),"=d"(d) : "c"(ctr) : );
#else
  __asm(".byte 0x0f, 0x01, 0xd0" : "=a"(a),"=d"(d) : "c"(ctr) : );
#endif
  return a | (uint64_t(d) << 32);
#else  // #elif defined (_MSC_FULL_VER) || (defined (__INTEL_COMPILER)...) // other compiler. try inline assembly with masm/intel/MS syntax
  uint32_t a, d;
  __asm {
    mov ecx, ctr
    _emit 0x0f
    _emit 0x01
    _emit 0xd0 ; // xgetbv
    mov a, eax
      mov d, edx
  }
  return a | (uint64_t(d) << 32);
#endif
}

#define BIT_HAS_MMX                    (1 << 23)
#define BIT_HAS_SSE                    (1 << 25)
#define BIT_HAS_SSE2                   (1 << 26)
#define BIT_HAS_SSE3                   (1 <<  0)
#define BIT_HAS_SSSE3                  (1 <<  9)
#define BIT_HAS_SSE41                  (1 << 19)
#define BIT_HAS_SSE42                  (1 << 20)
#define BIT_HAS_SSE4a                  (1 <<  6)
#define BIT_HAS_OSXSAVE                (1 << 27)
#define BIT_HAS_AVX                   ((1 << 28)|BIT_HAS_OSXSAVE)
#define BIT_HAS_AVX2                   (1 <<  5)
#define BIT_HAS_AVX512F                (1 << 16)
#define BIT_HAS_AVX512DQ               (1 << 17)
#define BIT_HAS_AVX512BW               (1 << 30)
#define BIT_HAS_FMA3                   (1 << 12)
#define BIT_HAS_FMA4                   (1 << 16)
#define BIT_HAS_X64                    (1 << 29)
#define BIT_HAS_XOP                    (1 << 11)

SIMDMode ConfigPars::getSIMD( const SIMDMode maxSIMD )
{
  SIMDMode  simd    = SIMD_SCALAR;
  int       regs[4] = {0, 0, 0, 0};

  do_cpuid( regs, 0 );
  if( regs[0] == 0 )                                return std::min<SIMDMode>(maxSIMD,simd);
  do_cpuid( regs, 1 );
  if( !(regs[2] & BIT_HAS_SSE41) )                  return std::min<SIMDMode>(maxSIMD,simd);
  simd = SIMD_SSE41;
  if( !(regs[2] & BIT_HAS_SSE42) )                  return std::min<SIMDMode>(maxSIMD,simd);
  do_cpuidex( regs, 1, 1 );
  if( !((regs[2] & BIT_HAS_AVX) == BIT_HAS_AVX ) )  return std::min<SIMDMode>(maxSIMD,simd); // first check if the cpu supports avx
  if( (xgetbv(0) & 6) != 6)                         return std::min<SIMDMode>(maxSIMD,simd); // then see if the os uses YMM state management via XSAVE etc...
  do_cpuidex( regs, 7, 0 );
  if( !(regs[1] & BIT_HAS_AVX2) )                   return std::min<SIMDMode>(maxSIMD,simd);
  simd = SIMD_AVX2;

  return std::min<SIMDMode>(maxSIMD,simd);
}
#else
SIMDMode ConfigPars::getSIMD( const SIMDMode maxSIMD )
{
  return SIMD_SCALAR;
}
#endif

