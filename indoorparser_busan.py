import xml.etree.ElementTree as ET
import math

class indoorgmlgraph():
    
    cellSpace = {}
    cellSpaceBoundary = {}
    state = {}
    transition = {}
    
    bound = []
    
    def __init__(self, IndoorPath):
        self.indoorgmlparser(IndoorPath)
          
    def getCellSpace(self):
        return self.cellSpace
    
    def getCellSpaceBoundary(self):
        return self.cellSpaceBoundary
    
    def getState(self):
        return self.state
    
    def getTransition(self):
        return self.transition
    
    def getBound(self):
        return self.bound
    
    def indoorgmlparser(self,IndoorPath):
         
        tree = ET.parse(IndoorPath)
        root = tree.getroot()
        
        primalSpaceFeatures = root[1]
        multiLayeredGraph = root[2]
        
        for child in primalSpaceFeatures[0]:
            
            if child.tag[-14:-6] == 'ellSpace':
                
                space = child[0]
                spaceName = space.tag
                indexS = spaceName.find('}')
                spaceName = spaceName[indexS+1:] #name of space(transition, general)
                spaceGmlId = list(space.attrib.values())[0] #gmlId
                
                tempjson = { 'cellType' : spaceName , 'partialboundedBy' : []}
                
                for item in space:
                    itemName = item.tag
                    indexI = itemName.find('}')
                    itemName = itemName[indexI+1:]
                    
                    if itemName in ['class','function','usage','description','name']:
                        tempjson[itemName] = " ".join(item.text.split()) #string attribute
                    elif itemName == 'duality':
                        tempjson[itemName] = list(item.attrib.values())[0][1:] #value inside tag without # character
                    elif itemName == 'partialboundedBy':
                        tempjson[itemName].append(list(item.attrib.values())[0][1:])
                    elif itemName == 'cellSpaceGeometry':
                        
                        if len(item[0][0]) > 1:
                            shellGeometry = []
                            for i in range(1,len(item[0][0])):
                                interiorShell = item[0][0][i][0]
                                
                                for surfaceMember in interiorShell:
                                
                                    lineString = surfaceMember[0][0][0]
                                    lineGeometry = []
                                    for p in lineString:
                                        coordinateP = " ".join(p.text.split()) #space, tab, newline removal
                                        lineGeometry.append(coordinateP)
                                    shellGeometry.append(lineGeometry)
                            tempjson['interiorCellSpaceGeometry'] = shellGeometry
                            
                        exteriorShell = item[0][0][0][0]
                        shellGeometry = []
                        for surfaceMember in exteriorShell:
                            
                            lineString = surfaceMember[0][0][0]
                            lineGeometry = []
                            for p in lineString:
                                coordinateP = " ".join(p.text.split()) #space, tab, newline removal
                                lineGeometry.append(coordinateP)
                            shellGeometry.append(lineGeometry)
                        tempjson['exteriorCellSpaceGeometry'] = shellGeometry
                        
                        
                if 'description' in tempjson:
                    indexFloor = tempjson['description'].find('storey=') + 8
                    tempjson['level'] = str(tempjson['description'][indexFloor]) #storey="2":indoor="elevator":
                        
                self.cellSpace[spaceGmlId] = tempjson
  
                
            elif child.tag[-14:-6] == 'Boundary':
                
                boundary = child[0]
                boundaryName = boundary.tag
                indexB = boundaryName.find('}')
                boundaryName = boundaryName[indexB+1:] #name of boundary(connection, anchor)
                boundaryGmlId = list(boundary.attrib.values())[0] #gmlId
                
                tempjson = { 'boundaryType' : boundaryName }
                
                for item in boundary:
                    itemName = item.tag
                    indexI = itemName.find('}')
                    itemName = itemName[indexI+1:]
                    
                    if itemName in ['description','name']:
                        tempjson[itemName] = " ".join(item.text.split())
                    elif itemName in ['duality']:
                        tempjson[itemName] = list(item.attrib.values())[0][1:]
                    elif itemName == 'cellSpaceBoundaryGeometry':
                        lineString = item[0][0][0][0]
                        surfaceGeometry = []
                        for p in lineString:
                            coordinateP = " ".join(p.text.split())
                            surfaceGeometry.append(coordinateP)  
                        tempjson[itemName] = surfaceGeometry
                        
                if 'description' in tempjson:
                    indexFloor = tempjson['description'].find('storey=') + 8
                    tempjson['level'] = str(tempjson['description'][indexFloor]) #storey="2":indoor="elevator":
                
                if 'duality' not in tempjson:
                    tempjson['duality'] = ''
                    
                self.cellSpaceBoundary[boundaryGmlId] = tempjson
                
        
        nodes = multiLayeredGraph[0][1][1][0][1]
        edges = multiLayeredGraph[0][1][1][0][2]
            
        for node in nodes:
            
            nodeName = node.tag
            indexN = nodeName.find('}')
            nodeName = nodeName[indexN+1:]
            
            if nodeName == 'boundedBy':
                continue
            
            elif nodeName == 'stateMember':
                
                state = node[0]
                stateGmlId = list(state.attrib.values())[0]
                
                tempjson = {'connects': []}
                
                for item in state:
                    
                    itemName = item.tag
                    indexI = itemName.find('}')
                    itemName = itemName[indexI+1:]
           
                    if itemName in ['description','name']:
                        tempjson[itemName] = " ".join(item.text.split())
                    elif itemName == 'connects':
                        tempjson[itemName].append(list(item.attrib.values())[0][1:])
                    elif itemName == 'duality':
                        tempjson[itemName] = list(item.attrib.values())[0][1:]
                    elif itemName == 'geometry':
                        tempjson[itemName] = " ".join(item[0][0].text.split())                      
                               
                self.state[stateGmlId] = tempjson

        
        for edge in edges:
            
            edgeName = edge.tag
            indexE = edgeName.find('}')
            edgeName = edgeName[indexE+1:]
            
            if edgeName == 'boundedBy':
                continue
            
            elif edgeName == 'transitionMember':
                
                transition = edge[0]
                transitionGmlId = list(transition.attrib.values())[0]
                
                tempjson = {'connects': []}
                
                for item in transition:
                    
                    itemName = item.tag
                    indexI = itemName.find('}')
                    itemName = itemName[indexI+1:]
                    
                    
                    if itemName in ['description','name']:
                        tempjson[itemName] = " ".join(item.text.split())
                    elif itemName == 'connects':
                        tempjson[itemName].append(list(item.attrib.values())[0][1:])
                    elif itemName == 'duality':
                        tempjson[itemName] = list(item.attrib.values())[0][1:]
                    elif itemName == 'geometry':
                        #tempjson[itemName] = [" ".join(item[0][0].text.split())," ".join(item[0][1].text.split())]
                        tempjson[itemName] = [" ".join(item[0][i].text.split()) for i in range(len(item[0]))]
                        weightByLength = [math.sqrt(pow((float(tempjson[itemName][i].split(' ')[0]) - float(tempjson[itemName][i+1].split(' ')[0])),2) + pow((float(tempjson[itemName][i].split(' ')[1]) - float(tempjson[itemName][i+1].split(' ')[1])),2) + pow((float(tempjson[itemName][i].split(' ')[2]) - float(tempjson[itemName][i+1].split(' ')[2])),2)) for i in range(len(tempjson[itemName])-1)]
                        tempjson['weight'] = sum(weightByLength)
                self.transition[transitionGmlId] = tempjson

            
graph = indoorgmlgraph('D:/development/indoor2neo4j/sampleNavi.gml')