import Card from 'react-bootstrap/Card'

const SeqCard =  ({sequence}) => {
  return (
    <Card>
      <Card.Body>
        <Card.Title>{sequence}</Card.Title>
        <Card.Text>{Object.values(sequence)}</Card.Text>
      </Card.Body>
    </Card>
  )
}

export default SeqCard;