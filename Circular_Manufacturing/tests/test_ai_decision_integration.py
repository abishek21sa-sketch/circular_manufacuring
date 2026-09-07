from circular_battery.ai.integration import PredictedCircularState,engineering_consequence
from circular_battery.data.demo import demo_chemistry

def test_more_circular_returns_reduce_virgin_requirement():
    low=PredictedCircularState(1000,150,.05,.05,.05,.20,.70)
    high=PredictedCircularState(1000,650,.05,.10,.15,.65,.10)
    a=engineering_consequence(demo_chemistry(),low,1000)
    b=engineering_consequence(demo_chemistry(),high,1000)
    assert b.virgin_requirement_kg < a.virgin_requirement_kg

def test_higher_scrap_changes_recovered_feed_state():
    a=PredictedCircularState(1000,300,.02,.1,.1,.6,.2)
    b=PredictedCircularState(1000,300,.08,.1,.1,.6,.2)
    ra=engineering_consequence(demo_chemistry(),a,1000)
    rb=engineering_consequence(demo_chemistry(),b,1000)
    assert rb.manufacturing_scrap_kg > ra.manufacturing_scrap_kg
