from neo4j import GraphDatabase
from indoorparser_sample import indoorgmlgraph
from os.path import basename

class indoor2neo(indoorgmlgraph):
    
    def __init__(self, IndoorPath):
        
        super().__init__(IndoorPath)
        self.buildingName = basename(IndoorPath)[:-4]    
        self.queryToNeo4j()
                           
    def addNode(self, nodeName, gmlId):
        
        queryList = []
        if nodeName == 'state':
            attr = self.state[gmlId]
            name = attr['name']
            duality = ""
            if 'duality' in attr:
                duality = attr['duality']
            geometry = attr['geometry'].split(' ')
            queryList = ["MERGE (s:",self.buildingName,":State {gmlId: '", str(gmlId), "'}) set s.name = '", name, "', s.location = point({x:toFloat(",geometry[0],"),y:toFloat(",geometry[1],"),z:toFloat(",geometry[2],")})"]
            
        elif nodeName == 'transition':
            attr = self.transition[gmlId]
            name = attr['name']
            weight = attr['weight']
            connects = attr['connects']
            duality = ""
            if 'duality' in attr:
                duality = attr['duality']
            queryList = ["MERGE (t:",self.buildingName,":Transition {gmlId: '", str(gmlId), "'}) set t.name = '", name, "', t.weight = toFloat(", str(weight), "), t.connects = ",str(connects)]
            
        elif nodeName == 'cellSpace':
            attr = self.cellSpace[gmlId]
            cellType = attr['cellType']
            partialboundedBy = attr['partialboundedBy']
            description = attr['description'].replace("\"","").replace("\'","")
            name = attr['name']
            duality = ""
            if 'duality' in attr:
                duality = attr['duality']
            indoorClass = attr['class']
            indoorFunction = attr['function']
            indoorUsage = attr['usage']
            level = attr['level']
            queryList = ["MATCH (l:Level) where l.level = '",str(level),"' MERGE (l)<-[:LEVEL]-(c:",self.buildingName,":CellSpace:",cellType," {gmlId: '", str(gmlId), "'}) set c.name = '", name, "', c.description = '", description, "', c.class = '", indoorClass, "', c.function = '",indoorFunction,
                         "', c.usage = '", indoorUsage, "', c.partialboundedBy = ", str(partialboundedBy)] + self.addGeometry('cellSpaceGeometry', gmlId)
            
        elif nodeName == 'CellSpaceBoundary':
            attr = self.cellSpaceBoundary[gmlId]
            boundaryType = attr['boundaryType']
            description = attr['description'].replace("\"","").replace("\'","")
            name = attr['name']
            duality = ""
            if 'duality' in attr:
                duality = attr['duality']
            level = attr['level']
            queryList = ["MATCH (l:Level) where l.level = '",str(level),"' MERGE (l)<-[:LEVEL]-(b:",self.buildingName,":CellSpaceBoundary:",boundaryType," {gmlId: '", str(gmlId), "'}) set b.name = '", name, "', b.description = '", description, "'"] + self.addGeometry('cellSpaceBoundaryGeometry', gmlId)
        
        elif nodeName == 'level':
            levelList = [self.cellSpace[key]['level'] for key in self.cellSpace] + [self.cellSpaceBoundary[key]['level'] for key in self.cellSpaceBoundary]
            sortedLevelList = sorted(set(levelList))
            queryList = ["WITH ", str(sortedLevelList), " AS levelList UNWIND levelList as l MERGE (n:Level {level : l})"]
                
        
        # self.query = "".join(queryList)
        return "".join(queryList)
     
    
    def addGeometry(self, geometryType, gmlId):
        
        if geometryType == 'cellSpaceGeometry':
            
            geometry = self.cellSpace[gmlId]['exteriorCellSpaceGeometry']
            
            if 'interiorCellSpaceGeometry' in self.cellSpace[gmlId].keys():
                
                interiorGeometry = self.cellSpace[gmlId]['interiorCellSpaceGeometry']
                
                return [" with c, ",str(geometry),"AS geometryList FOREACH (geometry in geometryList | merge (c)-[r:HAS_GEOMETRY]->(g:",self.buildingName,":Geometry:CellSpaceGeometry:exterior {gmlId: '", str(gmlId), "-' + randomUUID()}) FOREACH (geo in geometry | set g.geometry = coalesce(g.geometry,[]) + point({x:toFloat(split(geo,' ')[0]),y:toFloat(split(geo,' ')[1]),z:toFloat(split(geo,' ')[2])})))",
                        " with c, ",str(interiorGeometry),"AS interiorgeometryList FOREACH (geometry in interiorgeometryList | merge (c)-[r:HAS_GEOMETRY]->(g:",self.buildingName,":Geometry:CellSpaceGeometry:interior {gmlId: '", str(gmlId), "-' + randomUUID()}) FOREACH (geo in geometry | set g.geometry = coalesce(g.geometry,[]) + point({x:toFloat(split(geo,' ')[0]),y:toFloat(split(geo,' ')[1]),z:toFloat(split(geo,' ')[2])})))"]

            return [" with c, ",str(geometry),"AS geometryList FOREACH (geometry in geometryList | merge (c)-[r:HAS_GEOMETRY]->(g:",self.buildingName,":Geometry:CellSpaceGeometry:exterior {gmlId: '", str(gmlId), "-' + randomUUID()}) FOREACH (geo in geometry | set g.geometry = coalesce(g.geometry,[]) + point({x:toFloat(split(geo,' ')[0]),y:toFloat(split(geo,' ')[1]),z:toFloat(split(geo,' ')[2])})))"]
            #return [" with c, ",str(geometry),"AS geometry UNWIND geometry as geometryList MERGE (c)-[r:HAS_GEOMETRY]->(g:",self.buildingName,":Geometry:CellSpaceGeometry {gmlId: '", str(gmlId), "-' + randomUUID()}) set g.geometry = geometryList"]
     
        elif geometryType == 'cellSpaceBoundaryGeometry':
            
            geometry = self.cellSpaceBoundary[gmlId]['cellSpaceBoundaryGeometry']
            return [" with b MERGE (b)-[:HAS_GEOMETRY]->(g:",self.buildingName,":Geometry:CellSpaceBoundaryGeometry {gmlId: '", str(gmlId), "'}) with g, ",str(geometry),"AS geometry FOREACH (geo in geometry | set g.geometry = coalesce(g.geometry,[]) + point({x:toFloat(split(geo,' ')[0]),y:toFloat(split(geo,' ')[1]),z:toFloat(split(geo,' ')[2])}))"]
            #return [" with b MERGE (b)-[:HAS_GEOMETRY]->(g:",self.buildingName,":Geometry:CellSpaceBoundaryGeometry {gmlId: '", str(gmlId), "'}) set g.geometry = ", str(geometry)]
    
    
    def addDualityRelationship(self, label, multiIds):
        
        queryList = []
        if label == 'state':
            queryList = ["MATCH (s:",self.buildingName,":State) WHERE s.gmlId in ", str(multiIds), " with s MATCH (c:CellSpace) where c.gmlId = s.duality with c,s MERGE (s)-[:DUALITY]->(c)"]
        
        elif label == "transition":
            queryList = ["MATCH (t:",self.buildingName,":Transition) WHERE t.gmlId in ", str(multiIds), " with t MATCH (b:CellSpaceBoundary) where b.gmlId = t.duality with b,t MERGE (t)-[:DUALITY]->(b)"]
        return "".join(queryList)
        
    
    def addPartialRelationship(self):
        return "".join(["MATCH (c:",self.buildingName,":CellSpace) MATCH (b:",self.buildingName, ":CellSpaceBoundary)-[:HAS_GEOMETRY]-(gb:Geometry) WHERE b.gmlId in c.partialboundedBy MERGE (c)-[:PARTIALBOUNDEDBY]->(gb)"])
    
    
    def addPath(self, transitionGmlIds):
        return "".join(["MATCH (t:",self.buildingName,":Transition) WHERE t.gmlId in ", str(transitionGmlIds), " with t MATCH (s:", self.buildingName, ":State) WHERE s.gmlId = t.connects[0] MATCH (s2:", self.buildingName, ":State) WHERE s2.gmlId = t.connects[1] with s,s2,t MERGE (s)-[:PATH {weight : t.weight}]->(s2) MERGE (s)-[:CONNECTS]->(t)<-[:CONNECTS]-(s2)"])
        
        
    def queryToNeo4j(self):
        
       # Make sure the database is started first, otherwise attempt to connect will fail
        try:
            driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "pw"))
            print('SUCCESS: Connected to the Neo4j Database.')
        except Exception as e:
            print('ERROR: Could not connect to the Neo4j Database. See console for details.')
            raise SystemExit(e)
        
        session = driver.session()
        
        queryLevel = self.addNode('level',None)
        session.run(queryLevel)
        
        for gmlId in self.state:
            
            queryAddState = self.addNode('state',gmlId)
            session.run(queryAddState)
            
            if 'duality' in self.state[gmlId]:    
                dualityCellSpaceGmlId = self.state[gmlId]['duality']
                queryAddCellSpace = self.addNode('cellSpace', dualityCellSpaceGmlId)
                session.run(queryAddCellSpace)
                
        stateIds = list(self.state.keys())
        queryDualityConnection = self.addDualityRelationship('state', stateIds)
        session.run(queryDualityConnection)
        
        for gmlId in self.transition:

            queryAddTransition = self.addNode('transition',gmlId)
            session.run(queryAddTransition)
            
            if 'duality' in self.transition[gmlId]:
                dualityCellSpaceBoundaryGmlId = self.transition[gmlId]['duality']
                queryAddCellSpaceBoundary = self.addNode('CellSpaceBoundary', dualityCellSpaceBoundaryGmlId)
                session.run(queryAddCellSpaceBoundary)
                
        for gmlId in self.cellSpaceBoundary:
            
            if self.cellSpaceBoundary[gmlId]['duality'] == '' and self.cellSpaceBoundary[gmlId]['boundaryType'] == 'ConnectionBoundary':
                
                queryAddCellSpaceBoundary = self.addNode('CellSpaceBoundary', gmlId)
                session.run(queryAddCellSpaceBoundary)

        transitionGmlIds = list(self.transition.keys())
        queryDualityConnection = self.addDualityRelationship('transition', transitionGmlIds)
        queryPathConnection = self.addPath(transitionGmlIds)
        
        session.run(queryDualityConnection)
        session.run(queryPathConnection)
        
        for gmlId in self.cellSpaceBoundary:
            
            boundaryType = self.cellSpaceBoundary[gmlId]['boundaryType']
            
            if boundaryType == 'AnchorBoundary':
                queryAddCellSpaceBoundary = self.addNode('CellSpaceBoundary', gmlId)
                session.run(queryAddCellSpaceBoundary)
        
        #cellSpaceGmlIds = list(self.cellSpace.keys())
        queryPartialConnection = self.addPartialRelationship()
        session.run(queryPartialConnection)
        
        driver.close()
        
        
  
    
    