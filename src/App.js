import React, { useState } from 'react';
import Chess from "react-chess";
import Websocket from 'react-websocket';

const Information = props => {
return (<nav>
  <div style={{"display": "inline-block", width: "30%"}}>
    Previous winner: {props.winner ? "Black" : "White"}
  </div>
  <div style={{"display": "inline-block", width: "30%"}}>
    Current player: {props.player}
  </div>
  <div style={{"display": "inline-block", width: "30%"}}>
    Current evaluation: {props.score}
  </div>
</nav>)
}

function App() {
  const [pieces, setPieces] = useState(Chess.getDefaultLineup())

  const [winner, setWinner] = useState(null)
  const [player, setPlayer] = useState(null)
  const [score, setScore] = useState(null)

  const handleMessage = message => {
    const data = JSON.parse(message)
    switch (data.type) {
      case "player":
        setPlayer(data.player)
        break;
      case "update":
        setScore(data.score)
        console.log("Setting score to", data.score)
        setPieces(data.pieces)
        break;
      case "winner":
        setWinner(data.winner)
        break;
      default:
        console.log("Received message of unknown type: ", data)
    }
  }

  return (
    <div>
      <Information winner={winner} player={player} score={score}/>
      <Chess allowMoves={false} pieces={pieces}/>
      <Websocket url='ws://localhost:7000/chess_game' onMessage={handleMessage}/>
    </div>
  );
}

export default App;
