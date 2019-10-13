from colorfight import Colorfight
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST, HOME_COST, BLD_HOME
import math
import random

def play_game(
        game, \
        room     = 'public', \
        username = 'potato', \
        password = 'fatty'):

    game.connect(room = 'public')

    if game.register(username = username, \
            password = password):
        #set energyCount is the number of energy wells built when the house is destroyed, roundCount = number of rounds passed
        energyCount = 0
        roundCount = 0
        while True:
            #list of cells on perimeter of captured area, homeList = list of all homes in field
            perimeterList = []
            homeList = []
            cmd_list = []
            my_attack_list = []
            
            if not game.update_turn():
                break
    
            if game.me == None:
                continue
    
            me = game.me
            
            #weAreNotHomeless = has home been destroyed, buildEnergy = boolean value of whether energy needs to be built after home destruction
            weAreNotHomeless = False
            buildEnergy = True
            
            #iterate through the whole map and find the homes and append to homeList
            for i in range(0, 30):
                for j in range(0, 30):
                    c = game.game_map[(i,j)]
                    if c.building.name == "home" and (i, j):
                        homeList.append((i, j))
            
            #check if homeList contains our home, if it does, we are NOT homeless
            if len(homeList) >= 0:
                for obj in homeList:
                    if game.game_map[(obj[0], obj[1])].owner == game.uid:
                        weAreNotHomeless = True
                        buildEnergy = False
            
            #tempList lists owner of each cell, check intersection between idList and tempList, tempList holds OUR uid, if TRUE then append to perimeterList
            tempList = []
            idList = [game.uid]
            cellList = list(game.me.cells.values())
            
            #without randomization, the cell captures tend to the top-left
            #for each cell we own, look at the surrounding cells and append its owner to tempList
            random.shuffle(cellList)
            for cell in game.me.cells.values():
                for pos in cell.position.get_surrounding_cardinals():
                    c = game.game_map[pos]
                    tempList.append(c.owner)
                if(lambda idList, tempList: any(i in tempList for i in idList)):
                    perimeterList.append(cell)
                tempList = []

            #check if cell is in perimeterList and check if emergency procedure required
            for cell in cellList:
                houseBuildReq = (weAreNotHomeless == False and cell.owner == me.uid and me.gold >= HOME_COST[0])
                energyBuildReq = (weAreNotHomeless == True and cell.owner == me.uid and buildEnergy == True and me.gold >= BUILDING_COST[0] and cell.building.is_empty)
                #decide whether to build fortresses
                tempList = [game.game_map[pos].owner for pos in cell.position.get_surrounding_cardinals()]
                    
                if cell in perimeterList:
                    posList = list(cell.position.get_surrounding_cardinals())
                    #again, picks random position to expand into
                    random.shuffle(posList)
                    for pos in posList:
                        c = game.game_map[pos]
                        #if house needs to be rebuilt, build energy supply after destruction
                        if houseBuildReq:
                            print("Rebuilding House")
                            housePosition = random.choice(list(game.me.cells.values()))
                            housePosition = housePosition.position
                            building = BLD_HOME
                            cmd_list.append(game.build(housePosition, building))
                            me.gold -= HOME_COST[0]
                            weAreNotHomeless = True
                        if energyBuildReq:
                            print("Rebuilding Energy")
                            building = BLD_ENERGY_WELL
                            cmd_list.append(game.build(pos, building))
                            me.gold -= BUILDING_COST[0]
                            energyCount += 1
                            if energyCount >= int((len(list(game.me.cells.values()))) * 0.8):
                                buildEnergy = False
                        
                        #prioritize attacking a home above others
                        if c.attack_cost < me.energy and c.owner != game.uid \
                            and c.owner != 0 and c.position not in my_attack_list \
                            and c.building.name == "home":
                            cmd_list.append(game.attack(pos, c.attack_cost))
                            me.energy -= c.attack_cost
                            my_attack_list.append(c.position)
                        #expand if available
                        if c.attack_cost < me.energy and c.owner != game.uid \
                            and c.position not in my_attack_list:
                            print("Attacking Square Early Game")
                            cmd_list.append(game.attack(pos, c.attack_cost))
                            me.energy -= c.attack_cost
                            my_attack_list.append(c.position)
                    
                #"BUILDING PHASE" if can upgrade, then upgrade, if roundCount < 300 or we own less than 1/2 board, UPGRADE
                print("Building Phase")
                if cell.building.can_upgrade and \
                    (cell.building.is_home or cell.building.level < me.tech_level) and \
                    cell.building.upgrade_gold < me.gold and \
                    cell.building.upgrade_energy < me.energy and (roundCount < 300 or len(me.cells) < 450):
                    print("upgrade")
                    cmd_list.append(game.upgrade(cell.position))
                    me.gold   -= cell.building.upgrade_gold
                    me.energy -= cell.building.upgrade_energy
                else:
                    #builds energy wells on moderately energy-rich cells (for less than 20 cells owned)
                    if(cell.owner == game.uid and cell.building.name == "empty" and me.gold >= BUILDING_COST[0] and len(me.cells) <= 20 and cell.natural_energy >= 4):
                        print("Building Energy Well")
                        building = BLD_ENERGY_WELL
                        cmd_list.append(game.build(cell.position, building))
                        me.gold -= BUILDING_COST[0]
                    
                    #check if natural energy is greater than natural gold to build an energy well (after cells > 20), moderately energy-rich
                    elif(cell.owner == game.uid and cell.building.name == "empty" and me.gold >= BUILDING_COST[0] and cell.natural_energy > cell.natural_gold and len(me.cells) > 20 and cell.natural_energy >= 3):
                        if(all((val == 0 or val == game.uid) for val in tempList)):
                            print("Building Energy Well")
                            building = BLD_ENERGY_WELL
                            cmd_list.append(game.build(cell.position, building))
                            me.gold -= BUILDING_COST[0]
                        else:
                            #build fortress when encountering enemy cell
                            print("Building Fortress")
                            building = BLD_FORTRESS
                            cmd_list.append(game.build(cell.position, building))
                            me.gold -= BUILDING_COST[0]
                    #check if natural gold exceeds natural energy to build a gold mine (after cells > 20), moderately gold-rich
                    elif(cell.owner == game.uid and cell.building.name == "empty" and me.gold >= BUILDING_COST[0] and cell.natural_energy < cell.natural_gold and len(me.cells) > 20 and cell.natural_gold >= 3):
                        if(all((val == 0 or val == game.uid) for val in tempList)):
                            print("Building Gold Mine")
                            building = BLD_GOLD_MINE
                            cmd_list.append(game.build(cell.position, building))
                            me.gold -= BUILDING_COST[0]
                        else:
                            #build fortress when encountering enemy cell
                            print("Building Fortress")
                            building = BLD_FORTRESS
                            cmd_list.append(game.build(cell.position, building))
                            me.gold -= BUILDING_COST[0]
                    #if gold AND energy are both < 3, then build GOLD MINE
                    elif(cell.owner == game.uid and cell.building.name == "empty" and me.gold >= BUILDING_COST[0] and roundCount >= 100):
                        print("Building Gold Mine")
                        building = BLD_GOLD_MINE
                        cmd_list.append(game.build(cell.position, building))
                        me.gold -= BUILDING_COST[0]
                    
            print("Finished")
            result = game.send_cmd(cmd_list)
            roundCount += 1      

    game.disconnect()

if __name__ == '__main__':
    game = Colorfight()

    room = 'public'

    # ==========================  Play game once ===========================
    play_game(
        game     = game, \
        room     = room, \
        username = 'potato', \
        password = 'wacko'
    )
    # ======================================================================

    # ========================= Run my bot forever =========================
    #while True:
    #    try:
    #        play_game(
    #            game     = game, \
    #            room     = room, \
    #            username = 'ExampleAI' + str(random.randint(1, 100)), \
    #            password = str(int(time.time()))
    #        )
    #    except Exception as e:
    #        print(e)
    #        time.sleep(2)
