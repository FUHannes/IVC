



#include "Common.h"
#include "Config.h"
#include "PSNRCalc.h"




int main( const int argc, const char** argv )
{
  try
  {
    ConfigPars  cfg ( argc, argv );
    PSNRCalc    calc( cfg );
    calc.calcPSNR   ( &std::cout, &std::cerr );
  }
  catch( const Message& m )
  {
    std::cerr << m.str() << std::endl;
    return 1;
  }
  catch( ... )
  {
    std::cerr << "Unspecified exception" << std::endl;
    return 1;
  }
  return 0;
}


