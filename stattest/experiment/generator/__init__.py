from stattest.experiment.generator.model import AbstractRVSGenerator
from stattest.experiment.generator.generators import BetaRVSGenerator, CauchyRVSGenerator, LaplaceRVSGenerator, \
    LogisticRVSGenerator, TRVSGenerator, TukeyRVSGenerator, Chi2Generator, GammaGenerator, WeibullGenerator, \
    TruncnormGenerator, LoConNormGenerator, ScConNormGenerator, MixConNormGenerator, GumbelGenerator, LognormGenerator

symmetric_generators = [BetaRVSGenerator(a=0.5, b=0.5), BetaRVSGenerator(a=1, b=1), BetaRVSGenerator(a=2, b=2),
                        CauchyRVSGenerator(t=0, s=0.5), CauchyRVSGenerator(t=0, s=1), CauchyRVSGenerator(t=0, s=2),
                        LaplaceRVSGenerator(t=0, s=1), LogisticRVSGenerator(t=2, s=2),
                        TRVSGenerator(df=1), TRVSGenerator(df=2), TRVSGenerator(df=4), TRVSGenerator(df=10),
                        TukeyRVSGenerator(lam=0.14), TukeyRVSGenerator(lam=0.5), TukeyRVSGenerator(lam=2),
                        TukeyRVSGenerator(lam=5), TukeyRVSGenerator(lam=10)]
asymmetric_generators = [BetaRVSGenerator(a=2, b=1), BetaRVSGenerator(a=2, b=5), BetaRVSGenerator(a=4, b=0.5),
                         BetaRVSGenerator(a=5, b=1),
                         Chi2Generator(df=1), Chi2Generator(df=2), Chi2Generator(df=4), Chi2Generator(df=10),
                         GammaGenerator(alfa=2, beta=2), GammaGenerator(alfa=3, beta=2), GammaGenerator(alfa=5, beta=1),
                         GammaGenerator(alfa=9, beta=1), GammaGenerator(alfa=15, beta=1),
                         GammaGenerator(alfa=100, beta=1), GumbelGenerator(mu=1, beta=2), LognormGenerator(s=1, mu=0),
                         WeibullGenerator(l=0.5, k=1), WeibullGenerator(l=1, k=2), WeibullGenerator(l=2, k=3.4),
                         WeibullGenerator(l=3, k=4)]
modified_generators = [TruncnormGenerator(a=-1, b=1), TruncnormGenerator(a=-2, b=2), TruncnormGenerator(a=-3, b=3),
                       TruncnormGenerator(a=-3, b=1), TruncnormGenerator(a=-3, b=2),
                       LoConNormGenerator(p=0.3, a=1), LoConNormGenerator(p=0.4, a=1), LoConNormGenerator(p=0.5, a=1),
                       LoConNormGenerator(p=0.3, a=3), LoConNormGenerator(p=0.4, a=3), LoConNormGenerator(p=0.5, a=3),
                       LoConNormGenerator(p=0.3, a=5), LoConNormGenerator(p=0.4, a=5), LoConNormGenerator(p=0.5, a=5),
                       ScConNormGenerator(p=0.05, b=0.25), ScConNormGenerator(p=0.10, b=0.25),
                       ScConNormGenerator(p=0.20, b=0.25), ScConNormGenerator(p=0.05, b=2),
                       ScConNormGenerator(p=0.10, b=2),
                       ScConNormGenerator(p=0.20, b=2), ScConNormGenerator(p=0.05, b=4),
                       ScConNormGenerator(p=0.10, b=4),
                       ScConNormGenerator(p=0.20, b=4),
                       MixConNormGenerator(p=0.3, a=1, b=0.25), MixConNormGenerator(p=0.4, a=1, b=0.25),
                       MixConNormGenerator(p=0.5, a=1, b=0.25), MixConNormGenerator(p=0.3, a=3, b=0.25),
                       MixConNormGenerator(p=0.4, a=3, b=0.25), MixConNormGenerator(p=0.5, a=3, b=0.25),
                       MixConNormGenerator(p=0.3, a=1, b=4), MixConNormGenerator(p=0.4, a=1, b=4),
                       MixConNormGenerator(p=0.5, a=1, b=4), MixConNormGenerator(p=0.3, a=3, b=4),
                       MixConNormGenerator(p=0.4, a=3, b=4), MixConNormGenerator(p=0.5, a=3, b=4)]